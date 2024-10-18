import hashlib
import time
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


def get_owner_folder(role: str, role_id: str):
    return '/'.join([role, role_id])


def generate_sign(serial_num: str, owner_folder: str):
    target = serial_num + owner_folder

    # Encode the string to bytes
    byte_data = target.encode('utf-8')

    # Compute the MD5 hash
    result = hashlib.md5(byte_data)

    # Return top 10 chars of the hexadecimal representation of the hash
    return result.hexdigest()[:10]


def get_signed_object_key(serial_num: str, owner_folder: str, filename: str) -> str:
    sign = generate_sign(serial_num, owner_folder)

    # the same filename uploaded in 1000000 secs will be overwritten
    ts = int(time.time() / 1000000)

    new_filename = '-'.join([sign, str(ts), filename])
    return '/'.join([owner_folder, new_filename])


def get_signed_overwritable_object_key(serial_num: str, owner_folder: str, filename: str):
    sign = generate_sign(serial_num, owner_folder)
    new_filename = '-'.join([sign, filename])
    return '/'.join([owner_folder, new_filename])


def parse_owner_folder(object_key: str):
    parts = object_key.split('/')
    return '/'.join(parts[:2])


def get_percent_usage(
    currently_used_mb: float,
    total_mb: float
):
    return round(currently_used_mb / total_mb * 100, 2)

def current_seconds():
    return int(time.time())
