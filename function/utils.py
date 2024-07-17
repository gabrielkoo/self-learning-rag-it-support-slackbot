import json
from logging import getLogger

logger = getLogger()
logger.setLevel('INFO')


def jsondumps(data, **kwargs) -> str:
    def _ignore_bytes(obj):
        if isinstance(obj, bytes):
            return '<bytes>'
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

    kwargs['ensure_ascii'] = False

    return json.dumps(data, default=_ignore_bytes, skipkeys=True, **kwargs)
