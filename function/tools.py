from typing import TYPE_CHECKING

import urllib3
from duckduckgo_search import DDGS
from fake_useragent import UserAgent

from rag_utils import (
    create_knowledge_db_record,
    search_knowledge_db_record,
)

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.type_defs import (
        ToolResultContentBlockOutputTypeDef,
        ToolSpecificationTypeDef,
    )
    from mypy_boto3_bedrock_runtime.literals import (
        DocumentFormatType,
        ImageFormatType,
    )

http = urllib3.PoolManager()
ua = UserAgent()
ddgs = DDGS()


def search_web(*, query: str) -> 'ToolResultContentBlockOutputTypeDef':
    results = ddgs.text(query, max_results=10)
    return {
        'json': {
            'results': results,
        }
    }


def retreive_url(*, url: str) -> 'ToolResultContentBlockOutputTypeDef':
    response = http.request('GET', url, headers={
        'User-Agent': ua.random,
    })
    content_type = response.headers.get('Content-Type', '').split(';')[0]
    content_primary_type = content_type.split('/')[0]
    content_secondary_type = (
        content_type.split('/')[1] if len(content_type.split('/')) > 1 else ''
    )

    if content_primary_type == 'image':
        image_format: 'ImageFormatType' = content_secondary_type if content_secondary_type in [
            'jpeg',
            'png',
            'gif',
            'webp',
        ] else 'jpeg'  # type: ignore
        return {
            'image': {
                'format': image_format,
                'source': {
                    'bytes': response.data,
                },
            }
        }
    elif content_type.startswith('application/json'):
        return {
            'text': response.data.decode('utf-8'),
        }
    elif content_type.startswith(('text/', 'application/')):
        doc_format: 'DocumentFormatType' = content_secondary_type if content_secondary_type in [
            'pdf',
            'csv',
            'doc',
            'docx',
            'xls',
            'xlsx',
            'html',
            'md',
        ] else 'txt'  # type: ignore
        return {
            'document': {
                # The name is not very helpful in this case, but it's better than nothing
                'name': 'document',
                'format': doc_format,
                'source': {
                    'bytes': response.data,
                },
            }
        }
    else:
        return {
            'text': f'Content-Type: {content_type}\nContent:\n{response.data.decode('utf-8')}',
        }


def snapshot_knowledge(*, content: str) -> 'ToolResultContentBlockOutputTypeDef':
    knowledge_id = create_knowledge_db_record(content)
    return {
        'json': {
            'knowledge_id': knowledge_id,
        }
    }


def search_knowledge_base(*, question: str) -> 'ToolResultContentBlockOutputTypeDef':
    records = search_knowledge_db_record(question)
    return {
        'json': {
            'records': records,
        }
    }


TOOL_SPECS: list['ToolSpecificationTypeDef'] = [
    {
        'name': 'search_web',
        'description': 'Search the web with DuckDuckGo for information.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': 'The query to search the web for.',
                    },
                },
                'required': ['query'],
            },
        },
    },
    {
        'name': 'retreive_url',
        'description': 'Retreive the content of a URL. Preferrably use with "search_web".',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'url': {
                        'type': 'string',
                        'description': 'The URL to retreive content from. Do not make up any URLs.',
                    },
                },
                'required': ['url'],
            },
        },
    },
    {
        'name': 'snapshot_knowledge',
        'description': 'Snapshot new knowledge into the knowledge database only when necessary. Only include meaningful information.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'content': {
                        'type': 'string',
                        'description': 'The knowledge base content to snapshot.',
                    },
                },
                'required': ['content'],
            },
        },
    },
    {
        'name': 'search_knowledge_base',
        'description': 'Search the knowledge base database for similar content.',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'question': {
                        'type': 'string',
                        'description': 'The question to search for.',
                    },
                },
                'required': ['question'],
            },
        },
    },
]

TOOL_MAPPING = {
    'search_web': search_web,
    'retreive_url': retreive_url,
    'snapshot_knowledge': snapshot_knowledge,
    'search_knowledge_base': search_knowledge_base,
}
