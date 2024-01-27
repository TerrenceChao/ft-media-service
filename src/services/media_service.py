import boto3
from typing import Callable, Dict, Any
from ..configs.exceptions import *
from ..configs.conf import *
from ..configs.constants import *
from ..models.dtos import UploadParamsDTO
from ..utils import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


CONTENT_LENGTH_RANGE = ['content-length-range',
                        MIN_FILE_BIT_SIZE, MAX_FILE_BIT_SIZE]


class MediaService:
    def __init__(self, s3_client: boto3.client, s3_resource: boto3.resource):
        self.s3_client = s3_client
        self.s3_resource = s3_resource

    def get_upload_params(
        self,
        params: UploadParamsDTO,
        get_object_key: Callable[[str, str, str], str]
    ) -> (Dict):
        owner_folder = get_owner_folder(params.role, params.role_id)
        currently_used_mb = self.__get_currently_used_mb(owner_folder)
        if currently_used_mb >= params.total_mb:
            raise ForbiddenException(
                msg=f'You are not allowed to upload more files, available sizes: {params.total_mb} MB')

        object_key = get_object_key(
            params.serial_num,
            owner_folder,
            params.filename
        )
        conditions = [
            CONTENT_LENGTH_RANGE,
            ['starts-with', '$Content-Type', params.mime_type]
        ]

        presigned_post = self.__gen_presigned_post(
            object_key, params.mime_type, conditions)
        presigned_post.update({
            'currently-used-mb': currently_used_mb,
            'total-available-mb': params.total_mb,
            'used-percentage': get_percent_usage(currently_used_mb, params.total_mb),
        })
        return presigned_post

    def __gen_presigned_post(
        self,
        object_key: str,
        mime_type: str,
        conditions: list,
    ):
        try:
            # get signed url for uploading
            presigned_post = self.s3_client.generate_presigned_post(
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

        return presigned_post

    def __get_currently_used_mb(
        self,
        owner_folder: str
    ):
        paginator = self.s3_client.get_paginator('list_objects')
        currently_used_bytes = 0
        for page in paginator.paginate(Bucket=FT_MEDIA_BUCKET, Prefix=owner_folder):
            for content in page.get('Contents', []):
                currently_used_bytes += content['Size']
        return round(currently_used_bytes / MB, 2)

    def remove(
        self,
        serial_num: str,
        object_key: str
    ) -> (Dict):
        owner_folder = parse_owner_folder(object_key)
        sign = generate_sign(serial_num, owner_folder)
        if not sign in object_key:
            raise ForbiddenException(
                msg='You are not allowed to remove the file')

        try:
            # remove the file
            obj = self.s3_resource.Object(FT_MEDIA_BUCKET, object_key)
            resp = obj.delete()
            # log.info(resp)

        except Exception as e:
            log.error('Error deleting file: %s', e)
            raise ServerException(msg='Failed to remove file')

        return {
            'deleted': '/'.join([STORAGE_HOST, object_key]),
        }
