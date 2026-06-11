from .settings import *
from django.core.exceptions import ImproperlyConfigured
import os

DEBUG = False
PA_USER = os.environ.get('PA_USER', 'ccespedesdevia1715')
ALLOWED_HOSTS = [PA_USER + '.pythonanywhere.com']

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-prod-7gH8kL2mN4pQ6rS9uV1wX3yZ5')

# Media files a Cloudinary (opcional, si no hay vars usa local)
CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
if CLOUD_NAME:
    INSTALLED_APPS.insert(0, 'cloudinary_storage')
    INSTALLED_APPS.append('cloudinary')
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUD_NAME,
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    }
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
