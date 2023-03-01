import io
import os
import base64
import hashlib
import boto3
from PIL import Image
from typing import List, Dict, Any
from fastapi import APIRouter, \
    Depends, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException

from ...exceptions.media_except import \
    ClientException, NotFoundException, ServerException
from ..res.response import res_success, res_err
import logging as log


log.basicConfig(filemode='w', level=log.INFO)


S3_HOST = os.getenv('S3_HOST', 'http://localhost:8000')
FT_MEDIA_BUCKET = os.getenv('FT_MEDIA_BUCKET', 'foreign-teacher-media')
s3_resource = boto3.resource('s3')

def get_object_key(role: str, user_id: str, filename: str):
    return '/'.join([role, user_id, filename])

async def get_s3_resource():
    return s3_resource

router = APIRouter(
    prefix='/media/users',
    tags=['Companies/Teachers\' Media'],
    responses={404: {'description': 'Not found'}},
)
    
@router.post('', status_code=201)
async def save(
    user_id: str = Query(...), 
    role: str = Query(...), 
    file: UploadFile = File(...),
    token: str = Header(...), current_region: str = Header(...),
    s3: boto3.resource = Depends(get_s3_resource),
):
    if role != 'teacher' and role != 'company':
        raise ClientException(msg="The 'role' should be 'teacher' or 'company'")
    
    file_bytes = await file.read()
    file_size = len(file_bytes)
    try:
        file_bytes = io.BytesIO(file_bytes)

        object_key = get_object_key(role, user_id, file.filename)
        name, ext = os.path.splitext(file.filename)
        bucket = s3.Bucket(FT_MEDIA_BUCKET)
        bucket.upload_fileobj(
            Key=object_key,
            Fileobj=file_bytes,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': ext[1:],
            },
        )

    except Exception as e:
        log.error(f'Error uploading file: {e}')
        raise ServerException(msg='Failed to upload file')

    return res_success(data={
        'url': '/'.join([S3_HOST, object_key]),
        'content_type': file.content_type,
        'file_size': file_size,
    })


@router.delete('')
def remove(
    user_id: str = Query(...), 
    role: str = Query(...), 
    file_path: str = Query(...), 
    token: str = Header(...), current_region: str = Header(...),
    s3: boto3.resource = Depends(get_s3_resource),
):
    try:
        # Delete the file
        object_key = '/'.join([role, user_id, file_path])
        obj = s3.Object(FT_MEDIA_BUCKET, object_key)
        resp = obj.delete()
        log.info(resp)

    except Exception as e:
        log.error(f'Error deleting file: {e}')
        raise ServerException(msg='Failed to remove file')

    return res_success(data={
        'url': '/'.join([S3_HOST, object_key]),
    })