import boto3
from fastapi import APIRouter, Depends, Query
from ...configs.s3 import get_s3_resource, get_s3_client
from ...configs.exceptions import ForbiddenException, ServerException
from ...configs.settings import FT_MEDIA_BUCKET, STORAGE_HOST, CDN_HOST, \
    MIN_FILE_BIT_SIZE, MAX_FILE_BIT_SIZE, URL_EXPIRE_SECS
from ...utils import generate_sign, get_signed_object_key, parse_owner_folder
from ..res.response import res_success
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


CONTENT_LENGTH_RANGE = ['content-length-range',
                        MIN_FILE_BIT_SIZE, MAX_FILE_BIT_SIZE]


router = APIRouter(
    prefix='/users',
    tags=['Companies/Teachers\' Media'],
    responses={404: {'description': 'Not found'}},
)


@router.get('/upload-params')
def upload_params(
    # it's unique, invariant & private, could be id/data/metadata
    serial_num: str = Query(...),
    role: str = Query(...),
    role_id: str = Query(...),
    filename: str = Query(...),
    mime_type: str = Query(...),
    s3_client: boto3.client = Depends(get_s3_client),
):
    object_key = get_signed_object_key(serial_num, role, role_id, filename)
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
            'media-link': f'{STORAGE_HOST}/{object_key}',
        })
    except Exception as e:
        log.error('Error deleting file: %s', e)
        raise ServerException(msg='Failed to get signed url for uploading')

    return res_success(data=presigned_post)


@router.delete('')
def remove(
    # it's unique, invariant & private, could be id/data/metadata
    serial_num: str = Query(...),
    object_key: str = Query(...),
    s3_resource: boto3.resource = Depends(get_s3_resource),
):
    owner_folder = parse_owner_folder(object_key)
    sign = generate_sign(serial_num, owner_folder)
    if not sign in object_key:
        raise ForbiddenException(msg='You are not allowed to remove the file')

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
