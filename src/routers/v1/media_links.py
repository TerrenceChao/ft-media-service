import boto3
from fastapi import APIRouter, Depends, Query
from ...configs.s3 import get_s3_resource, get_s3_client
from ...configs.exceptions import ForbiddenException, ServerException
from ...configs.conf import *
from ...configs.constants import *
from ...models.dtos import UploadParamsDTO
from ...services.media_service import MediaService
from ...utils import *
from ..req.validation import get_mime_type
from ..res.response import res_success
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


router = APIRouter(
    prefix='/users',
    tags=['Companies/Teachers\' Media'],
    responses={404: {'description': 'Not found'}},
)


_media_service = MediaService(
    s3_client=get_s3_client(),
    s3_resource=get_s3_resource()
)


@router.get('/upload-params')
def upload_params(
    # it's unique, invariant & private, could be id/data/metadata
    serial_num: str = Query(...),
    role: str = Query(...),
    role_id: str = Query(...),
    filename: str = Query(...),
    mime_type: str = Depends(get_mime_type),
    total_mb: float = Query(MAX_TOTAL_MB),
    s3_client: boto3.client = Depends(get_s3_client),
):
    params = UploadParamsDTO(
        serial_num=serial_num,
        role=role,
        role_id=role_id,
        filename=filename,
        mime_type=mime_type,
        total_mb=total_mb,
    )
    presigned_post = _media_service.get_upload_params(
        params=params,
        get_object_key=get_signed_object_key,
    )
    return res_success(data=presigned_post)


@router.get('/upload-params/overwritable')
def overwritable_upload_params(
    # it's unique, invariant & private, could be id/data/metadata
    serial_num: str = Query(...),
    role: str = Query(...),
    role_id: str = Query(...),
    filename: str = Query(...),
    mime_type: str = Depends(get_mime_type),
    total_mb: float = Query(MAX_TOTAL_MB),
    s3_client: boto3.client = Depends(get_s3_client),
):
    params = UploadParamsDTO(
        serial_num=serial_num,
        role=role,
        role_id=role_id,
        filename=filename,
        mime_type=mime_type,
        total_mb=total_mb,
    )
    presigned_post = _media_service.get_upload_params(
        params=params,
        get_object_key=get_signed_overwritable_object_key,
    )
    return res_success(data=presigned_post)


@router.delete('')
def remove(
    # it's unique, invariant & private, could be id/data/metadata
    serial_num: str = Query(...),
    object_key: str = Query(...),
    s3_resource: boto3.resource = Depends(get_s3_resource),
):
    data = _media_service.remove(serial_num, object_key)
    return res_success(data=data)
