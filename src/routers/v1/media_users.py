import io
import os
import math
import base64
import boto3
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
ACCESS_KEY = os.getenv('ACCESS_KEY', None)
SECRET_ACCESS_KEY = os.getenv('SECRET_ACCESS_KEY', None)

try:
    session = boto3.Session(
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_ACCESS_KEY,
    )
    s3_resource = session.resource('s3')
except Exception as e:
    log.error('boto3.Session error, %s', e)
    s3_resource = boto3.resource('s3')


KB = 1024
MB = 1024 * KB


async def get_s3_resource():
    return s3_resource

# bucket = s3_resource.Bucket(FT_MEDIA_BUCKET)
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


async def parse_image_content(file_bytes: bytes):
    # Read the uploaded image as a PIL Image object
    image = Image.open(io.BytesIO(file_bytes))
    # Convert the PIL Image object to a byte stream
    image_bytes = io.BytesIO()
    format = image.format
    image.save(image_bytes, format=format)
    # Convert the byte stream to a string
    image_string = image_bytes.getvalue()
    image_string = image_string.decode('utf-8', errors='replace')
    return image_string


async def parse_base64_content(file_bytes: bytes):
    base64_string = base64.b64encode(file_bytes).decode('utf-8')
    return base64_string


PARSE_FILE_CONTENT = {
    'image/png': parse_base64_content,
    'image/jpeg': parse_base64_content, # for testing.. 'parse_base64_content' works!!!
    'image/jpg': parse_base64_content,
    'application/pdf': parse_base64_content,
}

async def read_image_stream(bucket_obj_body):
    image_string = bucket_obj_body.read().decode('utf-8')
    # Convert the image string to a byte stream
    image_bytes = io.BytesIO(image_string.encode('utf-8'))
    # Read the byte stream as a PIL Image object
    image = Image.open(image_bytes)
    # Convert the PIL Image object to a byte stream
    image_bytes = io.BytesIO()
    image.save(image_bytes, format=image.format)
    # Return the byte stream as a response
    image_bytes.seek(0)
    return image_bytes

async def read_base64_stream(bucket_obj_body):
    base64_string = bucket_obj_body.read().decode('utf-8')

    # Convert base64 string back to bytes
    base64_bytes = base64.b64decode(base64_string)

    # # Create a file stream from bytes
    base64_stream = io.BytesIO(base64_bytes)
    return base64_stream


READ_FILE_STREAM = {
    'image/png': read_base64_stream,
    'image/jpeg': read_base64_stream, # for testing.. 'parse_base64_content' works!!!
    'image/jpg': read_base64_stream,
    'application/pdf': read_base64_stream,
}


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
    
    content_type = file.content_type
    file_bytes = await file.read()
    file_size = len(file_bytes)
    if not 0 < file_size <= 2 * MB:
        raise ClientException(msg="Supported file size is 0 ~ 2 MB")
    
    try:
        if content_type in PARSE_FILE_CONTENT.keys():
            file_stream = await PARSE_FILE_CONTENT[content_type](file_bytes)
        else:
            file_stream = file_bytes
    except Exception as e:
        log.error('parse file content fail, %s', e)
        file_stream = file_bytes

    try:
        filename = urlquote(file.filename)
        object_key = get_object_key(role, user_id, filename)
        
        # Upload the file to S3
        s3.Bucket(FT_MEDIA_BUCKET).put_object(
            Key=object_key,
            Body=file_stream,
            ContentType=content_type,
            ACL='public-read'
        )

    except Exception as e:
        log.error('Error uploading file: %s', e)
        raise ServerException(msg='Failed to upload file')

    finally:
        file.file.close()

    return res_success(data={
        'url': f'{S3_HOST}/{object_key}',
        'content_type': content_type,
        'file_size': file_size,
    })


@router.get('/{role}/{user_id}/{filename}')
async def read_file(
    role: str,
    user_id: str, 
    filename: str,
    s3: boto3.resource = Depends(get_s3_resource),
):
    try:
        filename = urlquote(filename)
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
        
        # 3. read file stream
        try:
            if content_type in READ_FILE_STREAM.keys():
                file_stream = await READ_FILE_STREAM[content_type](obj.get()['Body'])
            else:
                file_stream = obj.get()['Body'].iter_chunks(chunk_size=4096)
        except Exception as e:
            file_stream = obj.get()['Body'].iter_chunks(chunk_size=4096)

        # Stream the object contents and encode each chunk as it is streamed
        return StreamingResponse(
            content=file_stream,
            headers={"Content-Disposition": 'inline'},
            media_type=content_type,
            # media_type='application/octet-stream',
        )
    
    except Exception as e:
        log.error('Error reading file: %s', e)
        raise ServerException(msg=f'Failed to read file, content_type:{content_type}, url:{url}, error:{e}')


'''
Works well with large files.
TODO:: needs to be improved for all types of files
'''
@router.get('/assets/{role}/{user_id}/{filename}')
async def read_file_stream(
    role: str,
    user_id: str, 
    filename: str,
    s3: boto3.resource = Depends(get_s3_resource),
):
    # get object from S3
    filename = urlquote(filename)
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
            log.error('Error reading file stream: %s', e)
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
        media_type=content_type,
        # media_type='application/octet-stream',
    )


# Deprecated
# @router.post('/base64', status_code=201)
async def upload_file_in_base64(
    user_id: str = Query(...), 
    role: str = Query(...), 
    file: UploadFile = File(...),
    token: str = Header(...), current_region: str = Header(...),
    s3: boto3.resource = Depends(get_s3_resource),
):
    if role != 'teacher' and role != 'company':
        raise ClientException(msg="The 'role' should be 'teacher' or 'company'")
    
    content_type = file.content_type
    file_bytes = await file.read()
    file_size = len(file_bytes)
    if not 0 < file_size <= 2 * MB:
        raise ClientException(msg="Supported file size is 0 ~ 2 MB")

    try:
        filename = urlquote(file.filename)
        object_key = get_object_key(role, user_id, filename)
        file_data = base64.b64encode(file_bytes).decode('utf-8')
        
        # Upload the file to S3
        s3.Bucket(FT_MEDIA_BUCKET).put_object(
            Key=object_key,
            Body=file_data,
            ContentType=content_type,
            ContentEncoding='base64',
            ACL='public-read'
        )

    except Exception as e:
        log.error('Error uploading file: %s', e)
        raise ServerException(msg='Failed to upload file')

    finally:
        file.file.close()

    return res_success(data={
        'url': f'{S3_HOST}/{object_key}',
        'content_type': content_type,
        'file_size': file_size,
    })
    

# Deprecated
# @router.get('/base64assets/{role}/{user_id}/{filename}')
async def read_file_in_base64(
    role: str,
    user_id: str, 
    filename: str,
    s3: boto3.resource = Depends(get_s3_resource),
):
    try:
        filename = urlquote(filename)
        url = f'{S3_HOST}/{role}/{user_id}/{filename}'
        log.info(url)
        # Retrieve the object from S3
        object_key = get_object_key(role, user_id, filename)
        obj = s3.Object(FT_MEDIA_BUCKET, object_key)

        # Get the content type of the object
        content_type = obj.content_type
        log.info(f'the content_type:{content_type}')

        file_string = obj.get()['Body'].read() #.decode('utf-8')
        file_bytes = base64.b64decode(file_string)
        file_stream = io.BytesIO(file_bytes)

        # Stream the object contents and encode each chunk as it is streamed
        return StreamingResponse(
            content=file_stream,
            headers={"Content-Disposition": 'inline'},
            media_type='application/octet-stream',
            # media_type=content_type,
        )
    
    except Exception as e:
        log.error('Error reading file: %s', e)
        raise ServerException(msg=f'Failed to read file, content_type:{content_type}, url: {url}, error:{e}')


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
        log.error('Error deleting file: %s', e)
        raise ServerException(msg='Failed to remove file')

    return res_success(data={
        'url': '/'.join([S3_HOST, object_key]),
    })