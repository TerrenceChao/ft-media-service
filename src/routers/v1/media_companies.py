import io
import os
import base64
import hashlib
from urllib.parse import urlparse
import boto3
from PIL import Image
from typing import List, Dict, Any
from fastapi import APIRouter, \
    Request, Depends, \
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

COMPANY = 'company'
def get_object_key(company_id: str, filename: str):
    return '/'.join([COMPANY, company_id, filename])

def get_rm_object_key(file_path: str):
    file_path = urlparse(file_path).path
    if file_path[0] == '/':
        return file_path[1:]
    
    return file_path

async def get_s3_resource():
    return s3_resource

router = APIRouter(
    prefix='/media/companies',
    tags=['Companies\' Media'],
    responses={404: {'description': 'Not found'}},
)

@router.post('/{company_id}/avatar', status_code=201)
async def save_avatar(
    company_id: str,
    file: UploadFile = File(...),
    token: str = Header(...), current_region: str = Header(...),
    s3: boto3.resource = Depends(get_s3_resource),
):
    file_bytes = await file.read()
    file_size = len(file_bytes)
    try:
        name, ext = os.path.splitext(file.filename)
        object_key = get_object_key(company_id, f'avatar{ext}')
        bucket = s3.Bucket(FT_MEDIA_BUCKET)
        bucket.upload_file(
            Key=object_key,
            Filename='./Netherlands.png',
            # ExtraArgs={
            #     'ACL': 'public-read',
            #     'ContentType': ext[1:],
            # },
        )

    except Exception as e:
        log.error(f'Error uploading file: {e}')
        raise ServerException(msg='Failed to upload avatar')

    return res_success(data={
        'url': '/'.join([S3_HOST, object_key]),
        'content_type': file.content_type,
        'file_size': file_size,
    })

@router.post('/{company_id}', status_code=201)
async def save(
    company_id: str,
    file: UploadFile = File(...),
    token: str = Header(...), current_region: str = Header(...),
    s3: boto3.resource = Depends(get_s3_resource),
):
    file_bytes = await file.read()
    file_size = len(file_bytes)
    try:
        # request_object_content = await file.read()
        # original_image = Image.open(io.BytesIO(request_object_content))
        # filtered_image = io.BytesIO()
        # original_image.save(filtered_image, 'JPEG')
        # filtered_image.seek(0)
        
        object_key = get_object_key(company_id, file.filename)
        file_data = await file.read()
        file_md5 = base64.b64encode(hashlib.md5(file_data).digest()).decode('utf-8')
        s3.Object(
            FT_MEDIA_BUCKET, 
            object_key,
        ).put(
            Body=file_data,
            ContentMD5=file_md5,
        )
        # bucket = s3.Bucket(FT_MEDIA_BUCKET)
        # bucket.put_object(
        #     Key=object_key,
        #     Body=file.file,
        #     ExtraArgs={
        #         'ACL': 'public-read',
        #         'ContentType': ext[1:],
        #     },
        # )

        
        # bucket = s3.Bucket(FT_MEDIA_BUCKET)
        # object_key = get_object_key(company_id, file.filename)
        # bucket.put_object(Key=object_key, Body=file.file, ContentType='JPEG')
        
        # request_object_content = await file.read()
        # img = Image.open(io.BytesIO(request_object_content))
        
        # image_format = None
        # if file.content_type == 'image/png':
        #     image_format = 'PNG'
        # elif (file.content_type == 'image/jpeg') or (file.content_type == 'image/jpg'):
        #     image_format = 'JPEG'

        # # Convert image to bytes
        # with io.BytesIO() as output:
        #     img.save(output, format=image_format)
        #     image_bytes = output.getvalue()

        # # Upload image to S3
        # bucket = s3.Bucket(FT_MEDIA_BUCKET)
        # object_key = get_object_key(company_id, 'file.filename')
        # bucket.put_object(Key=object_key, Body=image_bytes)

    except Exception as e:
        log.error(f'Error uploading file: {e}')
        raise ServerException(msg='Failed to upload file')

    return res_success(data={
        'url': '/'.join([S3_HOST, object_key]),
        'content_type': file.content_type,
        'file_size': file_size,
    })


@router.delete('/{company_id}')
def remove(
    company_id: str, 
    file_path: str,
    token: str = Header(...), current_region: str = Header(...),
    s3: boto3.resource = Depends(get_s3_resource),
):
    
    if not company_id in file_path:
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


# @router.post('/{company_id}/image', status_code=201)
# async def save(company_id: str, file: UploadFile = File(...)):
#     try:
#         file_bytes = await file.read()
#         img_bytes = io.BytesIO(file_bytes)
#         img_format = imghdr.what(file_bytes)
#         if img_format:
#             img = Image.open(io.BytesIO(file_bytes))
#             img_bytes = io.BytesIO()
#             img.save(img_bytes, format=img_format)
#         else:
#             log.error(f'Error open image: {file} is not a valid image')
#             raise ServerException(msg=f'This is not an image file: {file}')
    
#     except Exception as e:
#         log.error(f'Error transfer file to image: {e}')
#         raise ServerException(msg=e.__str__())


#     try:
#         object_key = get_object_key(company_id, file.filename)
        
#         # Upload the file
#         s3.upload_fileobj(
#             Bucket=FT_MEDIA_BUCKET,
#             Key=object_key,
#             Fileobj=img_bytes,
#             ExtraArgs={'ContentType': file.content_type}
#         )

#     except Exception as e:
#         log.error(f'Error uploading file: {e}')
#         raise ServerException(msg=e.__str__())
            
        
#     return res_success(data={
#         'url': '/'.join([S3_HOST, object_key]),
#         'content_type': file.content_type,
#     })
