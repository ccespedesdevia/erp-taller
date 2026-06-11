from .settings import *
import os

DEBUG = False
PA_USER = os.environ.get('PA_USER', 'ccespedesdevia1715')
PA_DOMAIN = PA_USER + '.pythonanywhere.com'
ALLOWED_HOSTS = [PA_DOMAIN]
CSRF_TRUSTED_ORIGINS = ['https://' + PA_DOMAIN]

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-prod-7gH8kL2mN4pQ6rS9uV1wX3yZ5')

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
