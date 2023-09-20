import os

# for media_links of routers
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

# for media_users of routers
S3_HOST = os.getenv('S3_HOST', 'http://localhost:8000')
ACCESS_KEY = os.getenv('ACCESS_KEY', None)
SECRET_ACCESS_KEY = os.getenv('SECRET_ACCESS_KEY', None)