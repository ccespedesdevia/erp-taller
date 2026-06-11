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

# Email SMTP (Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or 'noreply@cacdsoluciones.com'

# Notificaciones — correo del técnico
NOTIFICACIONES_EMAIL_TECNICO = [EMAIL_HOST_USER] if EMAIL_HOST_USER else []

# URL base para enlaces en correos
SEGUIMIENTO_URL = 'https://' + PA_DOMAIN
