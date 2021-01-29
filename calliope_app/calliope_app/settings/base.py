"""
Base settings of Django project.
"""
import os
import environ
from django.contrib.messages import constants as messages

env = environ.Env()

ROOT_DIR = (environ.Path(__file__) - 4)

# GENERAL
# ------------------------------------------------------------------------------
DEBUG = False

LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# URLS
# ------------------------------------------------------------------------------
WSGI_APPLICATION = 'calliope_app.wsgi.application'
ROOT_URLCONF = 'calliope_app.urls'
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = 'home'

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'api',
    'client',
    'taskmeta',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# PASSWORDS
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = False
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = 'SAMEORIGIN'

# STATIC
# ------------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = '/static'

# MEDIA
# ------------------------------------------------------------------------------
# Media files
MEDIA_URL = '/media/'

# MESSAGES
# --------------------------------------------------------------------------------
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# SPPOURT LANGUAGES
gettext = lambda s: s
LANGUAGES = [
    ('en', gettext('English')),
    ('es', gettext('Spanish')),
    # Add new langugage here
]

# MODELTRANSLATION
MODELTRANSLATION_LANGUAGES = ('en', 'es') # Add new language here
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_FALLBACK_LANGUAGES = ('en',)
MODELTRANSLATION_TRANSLATION_FILES = (
    'api.translation',
)

# LOCALE
LOCALE_PATHS = (
    os.path.join(ROOT_DIR, 'calliope_app', 'locale'),
)

## NREL API Key
NREL_API_EMAIL = env.str("NREL_API_EMAIL", "")
NREL_API_KEY = env.str("NREL_API_KEY", "")

## MAPBOX TOKEN
MAPBOX_TOKEN = env.str("MAPBOX_TOKEN", "")


# AWS
# --------------------------------------------------------------------------------
# AWS Credentials
AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY', None)

# SES EMAIL
AWS_SES_REGION_NAME = env.str('AWS_SES_REGION_NAME', '')
AWS_SES_REGION_ENDPOINT = env.str('AWS_SES_REGION_ENDPOINT', '')
AWS_SES_FROM_EMAIL = env.str('AWS_SES_FROM_EMAIL', '')

# S3 BUCKET
AWS_S3_BUCKET_NAME = env.str('AWS_S3_BUCKET_NAME', '')

# Cambium API
# ------------------------------------------------------------------------------
CAMBIUM_URL = env.str("CAMBIUM_URL", "")
CAMBIUM_API_KEY = env.str("CAMBIUM_API_KEY", "")
