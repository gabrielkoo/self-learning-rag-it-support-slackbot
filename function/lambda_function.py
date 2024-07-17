import traceback
from typing import TYPE_CHECKING

from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from slack_utils import (
    slack_app,
    load_slack_conversations,
)
from tools import TOOL_MAPPING
from utils import jsondumps, logger

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.type_defs import (
        ContentBlockTypeDef,
        ToolUseBlockTypeDef,
    )


@slack_app.event('message')
def handle_keywords(event: dict, say):
    channel = event['channel']
    ts = event['ts']
    thread_ts = event.get('thread_ts')
    reply_ts = thread_ts or ts
    bot_id = event.get('bot_id')

    # Do not "cross reply" other bots to avoid infinite conversations between bots
    if bot_id is not None:
        return

    conversations = load_slack_conversations(channel, reply_ts)

    # Lazy import to reduce cold start time
    from llm_utils import (
        construct_converse_messages,
        get_completion_response,
    )

    try:
        converse_message = construct_converse_messages(conversations)
        converse_messages = [converse_message]

        logger.info(jsondumps(converse_message))

        calls = 0

        while True:
            completion_response = get_completion_response(converse_messages, force_tool_use=calls == 0)
            completion_response_content: list['ContentBlockTypeDef'] = completion_response['content']  # type: ignore

            if len(list(filter(lambda x: 'toolUse' in x, completion_response_content))) > 0:
                converse_messages.append(completion_response)  # type: ignore
                response_content_blocks = []
                for content_block in completion_response_content:
                    if 'toolUse' in content_block:
                        tool_use: 'ToolUseBlockTypeDef' = content_block['toolUse']  # type: ignore
                        tool_use_id: str = tool_use['toolUseId']
                        tool_name: str = tool_use['name']
                        tool_input: dict = tool_use['input']  # type: ignore
                        tool_func = TOOL_MAPPING[tool_name]
                        logger.info(f'Using tool {tool_name} with input {tool_input}')
                        say(
                            channel=channel,
                            text=f'Tool `{tool_name}` used with input `{tool_input}`',
                            thread_ts=reply_ts,
                        )
                        try:
                            tool_result_content_block = tool_func(**tool_input)
                            if tool_name != 'retreive_url':
                                logger.info(f'Tool {tool_name} result: {tool_result_content_block}')
                            else:
                                logger.info(f'Tool {tool_name} called successfully.')
                            status = 'success'
                        except Exception as e:  # pylint: disable=broad-except
                            logger.exception(f'Error occured with tool {tool_name}: {traceback.format_exc()}')
                            tool_result_content_block = {
                                'text': f'Error: {e}',
                            }
                            status = 'error'

                        response_content_blocks.append({
                            'toolResult': {
                                'toolUseId': tool_use_id,
                                'content': [tool_result_content_block],
                                'status': status,
                            }
                        })

                if len(response_content_blocks) == 0:
                    raise Exception('No tool use processed')  # pylint: disable=broad-exception-raised

                converse_messages.append({
                    'role': 'user',
                    'content': response_content_blocks,
                })
            else:
                break

            calls += 1

        if len(completion_response_content) == 0:
            raise Exception(f'No completion response content - {completion_response_content}')
        response_text = completion_response_content[0]['text']  # type: ignore

        logger.info(f'Assistant reply: {response_text}')

        say(
            channel=channel,
            text=response_text,
            thread_ts=reply_ts,
        )
    except:  # pylint: disable=bare-except
        logger.exception(traceback.format_exc())
        say(
            channel=channel,
            text=f'An error occurred while processing the conversation.:\n```\n{traceback.format_exc()}\n```',
            thread_ts=reply_ts,
        )


def lambda_handler(event, context):
    if 'headers' not in event:
        return {'ok': False}
    elif (
        event['headers'].get('x-slack-retry-num') or
        event['headers'].get('X-Slack-Retry-Num')
    ):
        # Slack retries requests with exponential backoff
        # This avoids the duplicated processing of the same event
        return {
            'statusCode': 200,
            'body': 'ok',
        }

    slack_handler = SlackRequestHandler(slack_app)
    return slack_handler.handle(event, context)
