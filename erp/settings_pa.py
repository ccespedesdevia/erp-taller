from .settings import *
import os

DEBUG = False
PA_USER = os.environ.get('PA_USER', 'ccespedesdevia1715')
PA_DOMAIN = PA_USER + '.pythonanywhere.com'
ALLOWED_HOSTS = [PA_DOMAIN, 'www.cacdsoluciones.com', 'cacdsoluciones.com']
CSRF_TRUSTED_ORIGINS = ['https://' + PA_DOMAIN, 'https://www.cacdsoluciones.com', 'https://cacdsoluciones.com']

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-prod-7gH8kL2mN4pQ6rS9uV1wX3yZ5')

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email SMTP (Gmail) — configurar en Environmental Variables del dashboard
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or 'notificaciones@cacdsoluciones.com'

# A quién le llegan notificaciones al técnico
_tecno = os.environ.get('NOTIFICACIONES_EMAIL_TECNICO', '')
NOTIFICACIONES_EMAIL_TECNICO = [_tecno] if _tecno else ([EMAIL_HOST_USER] if EMAIL_HOST_USER else [])

SEGUIMIENTO_URL = 'https://' + PA_DOMAIN
API_BASE_URL = 'https://' + PA_DOMAIN
