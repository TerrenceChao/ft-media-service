import boto3
from .conf import ACCESS_KEY, SECRET_ACCESS_KEY
import logging as log

log.basicConfig(filemode='w', level=log.INFO)

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


def get_s3_resource():
    return s3_resource


def get_s3_client():
    return s3_client
