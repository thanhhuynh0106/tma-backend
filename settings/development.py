from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

CORS_ALLOW_ALL_ORIGINS = True

LOGGING['loggers']['django'] = {
    'handlers': ['console'],
    'level': 'INFO',
    'propagate': False,
}

LOGGING['loggers']['django.utils.autoreload'] = {
    'handlers': ['console'],
    'level': 'WARNING',
    'propagate': False,
}

# LOGGING['loggers']['django.utils.autoreload'] = {
#     'handlers': [],
#     'level': 'ERROR',
#     'propagate': False,
# }