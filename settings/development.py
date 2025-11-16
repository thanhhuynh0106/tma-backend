"""
Development settings.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']  # Cho phép tất cả trong dev

# CORS - Cho phép tất cả origins trong development
CORS_ALLOW_ALL_ORIGINS = True

# Logging - Chi tiết hơn trong development
LOGGING['loggers']['django']['level'] = 'DEBUG'