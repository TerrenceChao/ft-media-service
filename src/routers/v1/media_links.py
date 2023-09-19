import os
import boto3
import hashlib
import time
from fastapi import APIRouter, Depends, Query, HTTPException

from ...exceptions.media_except import \
    ClientException, NotFoundException, ServerException
from ..res.response import res_success
import logging as log


log.basicConfig(filemode='w', level=log.INFO)

FT_MEDIA_BUCKET = os.getenv('FT_MEDIA_BUCKET', 'foreign-teacher-media')
# for upload/delete (write)
STORAGE_HOST = os.getenv('STORAGE_HOST', f'https://{FT_MEDIA_BUCKET}.s3.amazonaws.com')
# for accelerate (read)
CDN_HOST = os.getenv('CDN_HOST', 'http://localhost:8000')
ACCESS_KEY = os.getenv('ACCESS_KEY', None)
SECRET_ACCESS_KEY = os.getenv('SECRET_ACCESS_KEY', None)
MIN_FILE_BIT_SIZE = int(os.getenv('MIN_FILE_BIT_SIZE', 1024))
MAX_FILE_BIT_SIZE = int(os.getenv('MAX_FILE_BIT_SIZE', 10485760))
URL_EXPIRE_SECS = int(os.getenv('URL_EXPIRE_SECS', 3600))

try:
    session = boto3.Session(
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_ACCESS_KEY,
    )
    s3_resource = session.resource('s3')
    s3_client = session.client('s3')
except Exception as e:
    log.error('boto3.Session error, %s', e)
    s3_resource = boto3.resource('s3')
    s3_client = boto3.client('s3')


async def get_s3_resource():
    return s3_resource

async def get_s3_client():
    return s3_client



def generate_hash(src: str):
    ts = str(time.time())
    target = src + ts
    
    # Encode the string to bytes
    byte_data = target.encode('utf-8')
    
    # Compute the MD5 hash
    result = hashlib.md5(byte_data)
    
    # Return the hexadecimal representation of the hash
    return result.hexdigest()

def get_object_hashed_key(role: str, role_id: str, filename: str):
    prefix = '/'.join([role, role_id])
    hash = generate_hash(prefix)
    new_filename = '-'.join([hash, filename])
    return '/'.join([prefix, new_filename])




CONTENT_LENGTH_RANGE = ['content-length-range', MIN_FILE_BIT_SIZE, MAX_FILE_BIT_SIZE]


router = APIRouter(
    prefix='/media/users',
    tags=['Companies/Teachers\' Media'],
    responses={404: {'description': 'Not found'}},
)


@router.get('/media_link')
def media_link(
    role: str = Query(...),
    role_id: str = Query(...),
    filename: str = Query(...),
    mime_type: str = Query(...),
    s3_client: boto3.client = Depends(get_s3_client),
):
    if role != 'teacher' and role != 'company':
        raise ClientException(msg="The 'role' should be 'teacher' or 'company'")
    
    object_key = get_object_hashed_key(role, role_id, filename)    
    conditions = [
        CONTENT_LENGTH_RANGE,
        ['starts-with', '$Content-Type', mime_type]
    ]
    
    try:
        # get signed url for uploading
        presigned_post = s3_client.generate_presigned_post(
            Bucket=FT_MEDIA_BUCKET,
            Key=object_key,
            Fields={
                'Content-Type': mime_type
            },
            Conditions=conditions,
            ExpiresIn=URL_EXPIRE_SECS
        )
        presigned_post.update({
            'media_link': f'{STORAGE_HOST}/{object_key}',
        })
    except Exception as e:
        log.error('Error deleting file: %s', e)
        raise ServerException(msg='Failed to get signed url for uploading')
    
    return res_success(data=presigned_post)


@router.delete('')
def remove(
    object_key: str = Query(...), 
    s3_resource: boto3.resource = Depends(get_s3_resource),
):
    try:
        # remove the file
        obj = s3_resource.Object(FT_MEDIA_BUCKET, object_key)
        resp = obj.delete()
        # log.info(resp)

    except Exception as e:
        log.error('Error deleting file: %s', e)
        raise ServerException(msg='Failed to remove file')

    return res_success(data={
        'deleted': '/'.join([STORAGE_HOST, object_key]),
    })