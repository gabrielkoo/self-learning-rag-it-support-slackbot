import json

import boto3

from db import create_db_record, get_db_records_by_embedding

EMBEDDING_MODEL_ID = 'amazon.titan-embed-text-v2:0'

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')


def create_embedding(input_text: str):
    accept = 'application/json'
    content_type = 'application/json'
    body = json.dumps({
        'inputText': input_text,
        'dimensions': 1024,
    })

    response = bedrock_runtime.invoke_model(
        body=body,
        modelId=EMBEDDING_MODEL_ID,
        accept=accept,
        contentType=content_type,
    )

    response_body = json.loads(response.get('body').read())
    return response_body['embedding']


def create_knowledge_db_record(content: str) -> str:
    embedding = create_embedding(content)
    result_id = create_db_record(content, embedding)
    return result_id


def search_knowledge_db_record(question: str) -> list:
    embedding = create_embedding(question)
    results = get_db_records_by_embedding(embedding)
    return results
