import io
import os
import math
import base64
import hashlib
import boto3
import shutil
from urllib.parse import quote as urlquote
from PIL import Image
from typing import List, Dict, Any
from fastapi import APIRouter, \
    Depends, \
    Cookie, Header, Path, Query, Body, Form, \
    File, UploadFile, status, \
    HTTPException
from fastapi.responses import Response, StreamingResponse


from ...exceptions.media_except import \
    ClientException, NotFoundException, ServerException
from ..res.response import res_success, res_err
import logging as log


log.basicConfig(filemode='w', level=log.INFO)


S3_HOST = os.getenv('S3_HOST', 'http://localhost:8000')
FT_MEDIA_BUCKET = os.getenv('FT_MEDIA_BUCKET', 'foreign-teacher-media')
s3_resource = boto3.resource('s3')

KB = 1024
MB = 1024 * KB

SUPPORTED_FILE_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'application/pdf': 'pdf',
}

async def get_s3_resource():
    return s3_resource

def get_s3_bucket():
    return s3_resource.Bucket(FT_MEDIA_BUCKET)

bucket = s3_resource.Bucket(FT_MEDIA_BUCKET)
async def s3_upload(file_bytes: bytes, object_key: str):
    s3_resource \
        .Bucket(FT_MEDIA_BUCKET) \
        .put_object(Key=object_key, Body=file_bytes)


async def s3_download(object_key: str):
    return s3_resource \
        .Object(FT_MEDIA_BUCKET, object_key) \
        .get()['Body'].read()


def get_object_key(role: str, user_id: str, filename: str):
    return '/'.join([role, user_id, filename])




router = APIRouter(
    prefix='/media/users',
    tags=['Companies/Teachers\' Media'],
    responses={404: {'description': 'Not found'}},
)
    
@router.post('', status_code=201)
async def upload_file(
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
    if not 0 < file_size <= 2 * MB:
        raise ClientException(msg="Supported file size is 0 ~ 2 MB")

    try:
        filename = urlquote(file.filename)
        object_key = get_object_key(role, user_id, filename)
        content_type = file.content_type
        log.info(f'the content_type:{content_type}')

        # Upload the file to S3
        s3.Bucket(FT_MEDIA_BUCKET).put_object(
            Key=object_key,
            Body=file_bytes,
            ContentType=content_type,
            ACL='public-read'
        )

    except Exception as e:
        log.error(f'Error uploading file: {e}')
        raise ServerException(msg='Failed to upload file')

    finally:
        file.file.close()

    return res_success(data={
        'url': f'{S3_HOST}/{object_key}',
        'content_type': content_type,
        'file_size': file_size,
    })


@router.get('/assets/{role}/{user_id}/{filename}')
async def read_file(
    role: str,
    user_id: str, 
    filename: str,
    s3: boto3.resource = Depends(get_s3_resource),
):
    content_type = None
    try:
        url = f'{S3_HOST}/{role}/{user_id}/{filename}'
        log.info(url)
        # Retrieve the object from S3
        object_key = get_object_key(role, user_id, filename)
        obj = s3.Object(FT_MEDIA_BUCKET, object_key)

        # Get the content type of the object
        content_type = obj.content_type
        log.info(f'the content_type:{content_type}')
        
        # # 1. Stream the object contents and encode each chunk as it is streamed
        # file_stream = io.BytesIO()
        # for chunk in obj.get()['Body'].iter_chunks(chunk_size=4096):
        #     file_stream.write(chunk)
        # # 2. download from s3
        # content = await s3_download(object_key)

        # Stream the object contents and encode each chunk as it is streamed
        return StreamingResponse(
            content=obj.get()['Body'].iter_chunks(chunk_size=4096),
            headers={"Content-Disposition": 'inline'},
            # media_type='application/octet-stream',
            media_type=content_type,
        )
    
    except Exception as e:
        log.error(f'Error reading file: {e}')
        raise ServerException(msg=f'Failed to read file, content_type:{content_type}, url:{url}, error:{e}')

   
@router.post('/base64', status_code=201)
async def upload_in_base64(
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
    if not 0 < file_size <= 2 * MB:
        raise ClientException(msg="Supported file size is 0 ~ 2 MB")

    content_type = None
    try:
        filename = urlquote(file.filename)
        object_key = get_object_key(role, user_id, filename)
        file_data = base64.b64encode(file_bytes).decode('utf-8')
        content_type = file.content_type
        
        # Upload the file to S3
        s3.Bucket(FT_MEDIA_BUCKET).put_object(
            Key=object_key,
            Body=file_data,
            ContentType=content_type,
            ContentEncoding='base64',
            ACL='public-read'
        )

    except Exception as e:
        log.error(f'Error uploading file: {e}')
        raise ServerException(msg='Failed to upload file')
    finally:
        file.file.close()

    return res_success(data={
        'url': f'{S3_HOST}/{object_key}',
        'content_type': content_type,
        'file_size': file_size,
    })
    

@router.get('/base64assets/{role}/{user_id}/{filename}')
async def read_file_in_base64(
    role: str,
    user_id: str, 
    filename: str,
    s3: boto3.resource = Depends(get_s3_resource),
):
    content_type = None
    try:
        url = f'{S3_HOST}/{role}/{user_id}/{filename}'
        log.info(url)
        # Retrieve the object from S3
        object_key = get_object_key(role, user_id, filename)
        obj = s3.Object(FT_MEDIA_BUCKET, object_key)

        # Get the content type of the object
        content_type = obj.content_type
        log.info(f'the content_type:{content_type}')

        # Stream the object contents and encode each chunk as it is streamed
        return StreamingResponse(
            content=obj.get()['Body'].iter_chunks(chunk_size=4096),
            headers={"Content-Disposition": 'inline'},
            media_type='application/octet-stream',
            # media_type=content_type,
        )
    
    except Exception as e:
        log.error(f'Error reading file: {e}')
        raise ServerException(msg=f'Failed to read file, content_type:{content_type}, url: {url}, error:{e}')


@router.get('/{role}/{user_id}/{filename}')
async def read_file_stream(
    role: str,
    user_id: str, 
    filename: str,
    s3: boto3.resource = Depends(get_s3_resource),
):
    # get object from S3
    object_key = get_object_key(role, user_id, filename)
    obj = s3.Object(FT_MEDIA_BUCKET, object_key)
    content_type = obj.content_type
    file_size = obj.content_length

    def file_chunks(chunk_size):
        for i in range(math.ceil(file_size / chunk_size)):
            chunk_start = i * chunk_size
            chunk_end = min((i + 1) * chunk_size - 1, file_size - 1)
            yield chunk_start, chunk_end

    async def stream_chunks():
        try:
            for chunk_start, chunk_end in file_chunks(1 * MB):
                range_header = f"bytes={chunk_start}-{chunk_end}"
                chunk = obj.get(Range=range_header)["Body"].read()
                yield chunk
        except Exception as e:
            log.error(f'Error reading file stream: {e}')
            url = f'{S3_HOST}/{role}/{user_id}/{filename}'
            raise ServerException(msg=f'Failed to read file, content_type:{content_type}, url:{url}, error:{e}')

    headers = {
        "Content-Disposition": 'inline',
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
    }
    return StreamingResponse(
        content=stream_chunks(),
        headers=headers,
        # media_type='application/octet-stream',
        media_type=content_type,
    )


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