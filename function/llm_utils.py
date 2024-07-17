from typing import TYPE_CHECKING

import boto3

from tools import (
    TOOL_SPECS,
)

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.type_defs import (
        ContentBlockTypeDef,
        ConverseResponseTypeDef,
        MessageTypeDef,
        MessageOutputTypeDef,
    )
    from mypy_boto3_bedrock_runtime.literals import (
        DocumentFormatType,
        ImageFormatType,
    )

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

MODEL_ID_SONNET_3 = 'anthropic.claude-3-sonnet-20240229-v1:0'
MODEL_ID_SONNET_3_5 = 'anthropic.claude-3-5-sonnet-20240620-v1:0'

SLACK_IMAGE_TYPE_TO_BEDROCK_IMAGE_TYPE: dict[str, 'ImageFormatType'] = {
    'jpg': 'jpeg',
    'png': 'png',
    'gif': 'gif',
    'webm': 'webp',
}
SLACK_FILETYPE_TO_BEDROCK_DOCUMENT_TYPE: dict[str, 'DocumentFormatType'] = {
    'pdf': 'pdf',
    'csv': 'csv',
    'doc': 'doc',
    'docx': 'docx',
    'xls': 'xls',
    'xlsx': 'xlsx',
    'html': 'html',
    'text': 'txt',
    'markdown': 'md',
}

SYSTEM_MESSAGE = '''You are a friendly helpful IT support Slack chatbot.
Always be polite and helpful, and assume you are replying to the user directly.
Users are specified in their Slack user ID format, e.g. `U12345678`.
To address the user, use `<@USER_ID>` in your response.

Only use simple Slack markdown formatting like `*bold*`, `_italic_`, `~strike~`, and `> quote`.

Always use Traditional Chinese (zh-TW) for your responses
unless the user specifies otherwise.

Do not include any search quality reflection/score, or do not include XML tags in your response.

If you used any tools and used their results in your response, please mention the source
URL/website/tool name in your response.

Do not assume the contents of any webpage/URL before using the tool to retrieve the content.

Prefer using knowledge base over the internet for answers.
Enrich your knowledge base for any new info you find on the internet
before using them in your responses.

For things that you are not sure, ask the user for more information or suggest
user to ask for help from a human IT staff.
'''


def construct_converse_messages(messages) -> 'MessageTypeDef':
    content_blocks: list['ContentBlockTypeDef'] = [{
        'text': 'Here is the conversation record between User & Support Bot:\n---\n',
    }]
    for message in messages:
        sender = message['sender']
        if attachments := message.get('attachments'):
            for attachment in attachments:
                filetype = attachment['filetype']
                if bedrock_image_type := SLACK_IMAGE_TYPE_TO_BEDROCK_IMAGE_TYPE.get(filetype):
                    content_blocks.append({
                        'image': {
                            'format': bedrock_image_type,
                            'source': {
                                'bytes': attachment['data'],
                            },
                        }
                    })
                elif bedrock_document_type := SLACK_FILETYPE_TO_BEDROCK_DOCUMENT_TYPE.get(filetype):
                    content_blocks.append({
                        'document': {
                            'format': bedrock_document_type,
                            'name': f'{bedrock_document_type} from {sender}',
                            'source': {
                                'bytes': attachment['data'],
                            },
                        },
                    })
                else:
                    content_blocks.append({
                        'text': f'Attachment from {sender}: {attachment["title"]} `{filetype}`',
                    })
        content_blocks.append({
            'text': f'{sender}: {message["message"]}',
        })
    content_blocks.append({
        'text': '\n---\nNow reply to the user.',
    })

    converse_message: 'MessageTypeDef' = {
        'role': 'user',
        'content': content_blocks,
    }
    return converse_message


def message_contains_document(message: 'MessageTypeDef') -> bool:
    if any(
        'document' in content_block
        for content_block in message['content']
    ):
        return True
    elif any(
        any(
            'document' in content
            for content in content_block['toolResult']['content']
        )
        for content_block in message['content']
        if 'toolResult' in content_block
    ):
        return True

    return False


def get_completion_response(messages: list, force_tool_use: bool = False) -> 'MessageOutputTypeDef':
    # Sonnet 3.5 does not support DocumentBlock yet as of early July 2024.
    # Ref: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html#conversation-inference-supported-models-features
    if any(message_contains_document(message) for message in messages):
        model_id = MODEL_ID_SONNET_3
    else:
        model_id = MODEL_ID_SONNET_3_5

    completion_response: ConverseResponseTypeDef = bedrock_runtime.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={
            'temperature': 0.1,
        },
        system=[{
            'text': SYSTEM_MESSAGE,
        }],
        toolConfig={
            'tools': [
                {
                    'toolSpec': tool
                }
                for tool in TOOL_SPECS
            ],
            'toolChoice': ({
                'any': {}
            } if force_tool_use else {
                'auto': {},
            }),
        },
    )
    output = completion_response['output']
    if 'message' not in output:
        return {
            'role': 'assistant',
            'content': [{
                'text': 'I am unable to generate a response at this time. Please try again later.',
            }],
        }
    return output['message']
