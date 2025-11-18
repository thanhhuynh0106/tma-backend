"""
Development settings.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# CORS - Cho phép tất cả origins trong development
CORS_ALLOW_ALL_ORIGINS = True

# Logging - Chi tiết hơn trong development nhưng filter autoreload
LOGGING['loggers']['django'] = {
    'handlers': ['console'],
    'level': 'INFO',  # Đổi từ DEBUG sang INFO
    'propagate': False,
}

# Filter autoreload messages
LOGGING['loggers']['django.utils.autoreload'] = {
    'handlers': ['console'],
    'level': 'WARNING',  # Chỉ log WARNING và ERROR
    'propagate': False,
}

# Hoặc disable hoàn toàn autoreload logger
# LOGGING['loggers']['django.utils.autoreload'] = {
#     'handlers': [],
#     'level': 'ERROR',
#     'propagate': False,
# }