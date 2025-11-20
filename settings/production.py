from .base import *

DEBUG = False

ALLOWED_HOSTS = get_env('ALLOWED_HOSTS', default='').split(',') if get_env('ALLOWED_HOSTS', default='') else []

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = get_env('CORS_ALLOWED_ORIGINS', default='').split(',') if get_env('CORS_ALLOWED_ORIGINS', default='') else []


SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True