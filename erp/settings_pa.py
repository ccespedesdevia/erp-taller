from .settings import *
import os

DEBUG = False
ALLOWED_HOSTS = [os.environ.get('PA_USER', '') + '.pythonanywhere.com']

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured('SECRET_KEY environment variable is required')

# Cloudinary
INSTALLED_APPS.insert(0, 'cloudinary_storage')
INSTALLED_APPS.append('cloudinary')

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
