from fastapi import APIRouter, Depends, Query
from ...configs.adapters import storage_adapter
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


_media_service = MediaService(storage_adapter)


@router.get('/upload-params')
async def upload_params(
    # it's unique, invariant & private, could be id/data/metadata
    serial_num: str = Query(...),
    role: str = Query(...),
    role_id: str = Query(...),
    filename: str = Query(...),
    mime_type: str = Depends(get_mime_type),
    total_mb: float = Query(MAX_TOTAL_MB),
    # s3_client: boto3.client = Depends(get_s3_client),
):
    params = UploadParamsDTO(
        serial_num=serial_num,
        role=role,
        role_id=role_id,
        filename=filename,
        mime_type=mime_type,
        total_mb=total_mb,
    )
    presigned_post = await _media_service.get_upload_params(
        params=params,
        get_object_key=get_signed_object_key,
    )
    return res_success(data=presigned_post)


@router.get('/upload-params/overwritable')
async def overwritable_upload_params(
    # it's unique, invariant & private, could be id/data/metadata
    serial_num: str = Query(...),
    role: str = Query(...),
    role_id: str = Query(...),
    filename: str = Query(...),
    mime_type: str = Depends(get_mime_type),
    total_mb: float = Query(MAX_TOTAL_MB),
    # s3_client: boto3.client = Depends(get_s3_client),
):
    params = UploadParamsDTO(
        serial_num=serial_num,
        role=role,
        role_id=role_id,
        filename=filename,
        mime_type=mime_type,
        total_mb=total_mb,
    )
    presigned_post = await _media_service.get_upload_params(
        params=params,
        get_object_key=get_signed_overwritable_object_key,
    )
    return res_success(data=presigned_post)


@router.delete('')
async def remove(
    # it's unique, invariant & private, could be id/data/metadata
    serial_num: str = Query(...),
    object_key: str = Query(...),
    # s3_client: boto3.client = Depends(get_s3_client),
):
    data = await _media_service.remove(serial_num, object_key)
    return res_success(data=data)
