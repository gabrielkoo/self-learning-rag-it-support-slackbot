import os

import urllib3
from slack_bolt import App

SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')

http = urllib3.PoolManager()

slack_app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    process_before_response=True,
)


def download_slack_attachment(url: str) -> bytes:
    resp = http.request(
        'GET',
        url,
        headers={'Authorization': f'Bearer {SLACK_BOT_TOKEN}'},
    )
    return resp.data


def get_attachments(message: dict) -> list:
    files = message.get('files', [])
    attachment_info = []
    for file in files:
        attachment_info.append({
            'title': file['title'],
            'mimetype': file['mimetype'],
            'filetype': file['filetype'],
            'data': download_slack_attachment(file['url_private_download']),
        })
    return attachment_info


def load_slack_conversations(channel: str, thread_ts: str) -> list:
    conversation = slack_app.client.conversations_replies(
        channel=channel,
        ts=thread_ts,
        limit=1000,  # This limit should probably not be hit
    )

    messages = []
    for slack_message in conversation.get('messages', []):
        if 'bot_id' not in slack_message:
            sender = slack_message.get('user', '')
        else:
            sender = slack_message['bot_profile']['name']
        text = slack_message.get('text', '')
        attachments = get_attachments(slack_message)

        message = {
            'sender': sender,
            'message': text,
        }
        if attachments:
            message['attachments'] = attachments
        messages.append(message)
    return messages
