"""
Django settings for testing.
"""
import os
import sys
from .base import *

# LOCAL ENVS
# ------------------------------------------------------------------------------
env = environ.Env()

SETTINGS_READ_ENV_FILE = env.str('DJANGO_SETTINGS_READ_ENV_FILE', True)
if SETTINGS_READ_ENV_FILE:
    env.read_env(str(ROOT_DIR.path(".env")))

# GENERAL
# ------------------------------------------------------------------------------
DEBUG = True
SECRET_KEY = env.str("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]

# DATABASES
# --------------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': env.str('POSTGRES_HOST'),
        'PORT': env.str('POSTGRES_PORT'),
        'USER': env.str('POSTGRES_USER'),
        'PASSWORD': env.str('POSTGRES_PASSWORD'),
        'NAME': env.str('POSTGRES_DB'),
    }
}

# DATA STORAGE
# ------------------------------------------------------------------------------
# volume & workdir
DATA_VOLUME = "/data"
DATA_STORAGE = env.str("DATA_STORAGE", DATA_VOLUME).rstrip("/")

# MEDIA
# ------------------------------------------------------------------------------
MEDIA_ROOT = DATA_STORAGE + "/"

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # noqa F405

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "api.engage.EmailBackend"

# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = "localhost"
# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = 1025

# LOGGING
# --------------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': sys.stdout,
        },
        'system': {
            'level': 'WARNING',
            'filters': ['require_debug_false'],
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': sys.stdout,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'system'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'MYAPP': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'celery.app.trace': {
            'handlers': [],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

# CELERY
# --------------------------------------------------------------------------------
CELERY_BROKER_URL = env.str('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE if USE_TZ else None
CELERY_TRACK_STARTED = True

# AWS
# --------------------------------------------------------------------------------
# AWS Credentials
AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY', '')

# SES EMAIL
AWS_SES_REGION_NAME = env.str('AWS_SES_REGION_NAME', '')
AWS_SES_REGION_ENDPOINT = env.str('AWS_SES_REGION_ENDPOINT', '')
AWS_SES_FROM_EMAIL = env.str('AWS_SES_FROM_EMAIL', '')

# STATICFILES
STATIC_ROOT = os.path.join(ROOT_DIR, 'staticfiles')
