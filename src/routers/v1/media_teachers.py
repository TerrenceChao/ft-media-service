import io
import os
import base64
from urllib.parse import urlparse
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

TEACHER = 'teacher'
def get_object_key(teacher_id: str, filename: str):
    return '/'.join([TEACHER, teacher_id, filename])

def get_rm_object_key(file_path: str):
    file_path = urlparse(file_path).path
    if file_path[0] == '/':
        return file_path[1:]
    
    return file_path

async def get_s3_resource():
    return s3_resource

router = APIRouter(
    prefix='/media/teachers',
    tags=['Teachers\' Media'],
    responses={404: {'description': 'Not found'}},
)

@router.post('/{teacher_id}/avatar', status_code=201)
async def save_avatar(
    teacher_id: str, 
    file: UploadFile = File(...),
    token: str = Header(...), current_region: str = Header(...),
    s3: boto3.resource = Depends(get_s3_resource),
):
    try:
        bucket = s3.Bucket(FT_MEDIA_BUCKET)
        name, ext = os.path.splitext(file.filename)
        filename = 'avatar' + ext
        object_key = get_object_key(teacher_id, filename)
        bucket.upload_fileobj(
            Key=object_key,
            Fileobj=file.file,
            ExtraArgs={
                'ACL': 'public-read',
            },
        )

    except Exception as e:
        log.error(f'Error uploading file: {e}')
        raise ServerException(msg='Failed to upload avatar')

    return res_success(data={
        'url': '/'.join([S3_HOST, object_key]),
        'content_type': file.content_type,
    })
        
@router.post('/{teacher_id}', status_code=201)
async def save(
    teacher_id: str, 
    file: UploadFile = File(...),
    token: str = Header(...), current_region: str = Header(...),
    s3: boto3.resource = Depends(get_s3_resource),
):
    try:
        file_bytes = await file.read()
        file_bytes = io.BytesIO(file_bytes)

        bucket = s3.Bucket(FT_MEDIA_BUCKET)
        object_key = get_object_key(teacher_id, file.filename)
        bucket.upload_fileobj(
            Key=object_key,
            Fileobj=file_bytes,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': file.content_type,
            },
        )

    except Exception as e:
        log.error(f'Error uploading file: {e}')
        raise ServerException(msg='Failed to upload file')

    return res_success(data={
        'url': '/'.join([S3_HOST, object_key]),
        'content_type': file.content_type,
    })


@router.delete('/{teacher_id}')
def remove(
    teacher_id: str, 
    file_path: str,
    token: str = Header(...), current_region: str = Header(...),
    s3: boto3.resource = Depends(get_s3_resource),
):
    
    if not teacher_id in file_path:
        raise ServerException(msg='not yours')

    try:
        # Delete the file
        object_key = get_rm_object_key(file_path)
        log.info(object_key)
        resp = s3.delete_object(
            Bucket=FT_MEDIA_BUCKET,
            Key=object_key,
        )

    except Exception as e:
        log.error(f'Error deleting file: {e}')
        raise ServerException(msg='Failed to remove file')

    return res_success(data={
        'url': '/'.join([S3_HOST, object_key]),
        'resp': resp
    })