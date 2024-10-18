import os

# probe cycle secs
PROBE_CYCLE_SECS = int(os.getenv("PROBE_CYCLE_SECS", 3))

# for media_links of routers
FT_MEDIA_BUCKET = os.getenv('FT_MEDIA_BUCKET', 'foreign-teacher-media')
S3_CONNECT_TIMEOUT=int(os.getenv("S3_CONNECT_TIMEOUT", 10))
S3_READ_TIMEOUT=int(os.getenv("S3_READ_TIMEOUT", 10))
S3_MAX_ATTEMPTS=int(os.getenv("S3_MAX_ATTEMPTS", 3))

# for upload/delete (write)
STORAGE_HOST = os.getenv('STORAGE_HOST', f'https://{FT_MEDIA_BUCKET}.s3.amazonaws.com')
# for accelerate (read)
CDN_HOST = os.getenv('CDN_HOST', 'http://localhost:8000')
ACCESS_KEY = os.getenv('ACCESS_KEY', None)
SECRET_ACCESS_KEY = os.getenv('SECRET_ACCESS_KEY', None)
MIN_FILE_BIT_SIZE = int(os.getenv('MIN_FILE_BIT_SIZE', 1024))
MAX_FILE_BIT_SIZE = int(os.getenv('MAX_FILE_BIT_SIZE', 2097152)) # 2 MB
URL_EXPIRE_SECS = int(os.getenv('URL_EXPIRE_SECS', 300)) # 5 mins
MAX_TOTAL_MB = float(os.getenv('MAX_TOTAL_MB', 8.0))

# for media_users of routers
S3_HOST = os.getenv('S3_HOST', 'http://localhost:8000')
ACCESS_KEY = os.getenv('ACCESS_KEY', None)
SECRET_ACCESS_KEY = os.getenv('SECRET_ACCESS_KEY', None)

# valid mime types
DEFAULT_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/bmp',
    'application/pdf',
    'text/plain',
}
VALID_MIME_TYPES = os.getenv('VALID_MIME_TYPES', None)

if VALID_MIME_TYPES is None:
    VALID_MIME_TYPES = DEFAULT_MIME_TYPES
else:
    VALID_MIME_TYPES = set([mine_type.strip() for mine_type in VALID_MIME_TYPES.split(',') if mine_type.strip() != ''])