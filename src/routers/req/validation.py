import mimetypes
from fastapi import Query
from ...configs.conf import *
from ...configs.exceptions import ClientException

def parse_mime_type(file_name):
    mime_type, encoding = mimetypes.guess_type(file_name)
    return mime_type


def get_mime_type(filename: str = Query(...)):
    mime_type = parse_mime_type(filename)
    if mime_type is None or not mime_type in VALID_MIME_TYPES:
        raise ClientException(msg='Unsupported file type, only support: ' + ', '.join(VALID_MIME_TYPES))
    
    return mime_type