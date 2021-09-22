from datetime import timedelta
from corsheaders.defaults import default_headers
from .base import *


PROJECT_APPS = [
    'corsheaders',
    'rest_framework',
    'django_filters',
    'taggit',
    'simple_history',

    'apps.person',
    'apps.feeder',
    'apps.notifier',
]

INSTALLED_APPS = INSTALLED_APPS + PROJECT_APPS


# https://docs.djangoproject.com/en/3.1/topics/auth/customizing/#auth-custom-user
AUTH_USER_MODEL = 'person.User'


# Specifying authentication backends
# https://docs.djangoproject.com/en/3.0/topics/auth/customizing/
AUTHENTICATION_BACKENDS = [
    # Allow login with email, username and msisdn
    'apps.person.helpers.AuthBackend',
]


# MIDDLEWARES
PROJECT_MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]
MIDDLEWARE = PROJECT_MIDDLEWARE + MIDDLEWARE


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
]


# Django Simple JWT
# ------------------------------------------------------------------------------
# https://github.com/davesque/django-rest-framework-simplejwt
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),
    'USER_ID_FIELD': 'uuid',
    'USER_ID_CLAIM': 'user_uuid',
}


# REDIS
REDIS_HOST = '127.0.0.1'
REDIS_PORT = '6379'
REDIS_URL = 'redis://' + REDIS_HOST + ':' + REDIS_PORT


# Django Rest Framework (DRF)
# ------------------------------------------------------------------------------
# https://www.django-rest-framework.org/
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',
        'user': '100/minute'
    },
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication'
    ],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'PAGE_SIZE': 25
}


# Django csrf
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/2.2/ref/csrf/
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_SAMESITE = None
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_SECURE = False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = [
    'localhost:4200',
]


# Django CORS
# ------------------------------------------------------------------------------
# https://pypi.org/project/django-cors-headers/
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:4200',
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    'ngsw-bypass',
    'Access-Control-Allow-Origin',
]


# Django-taggit
# https: // django-taggit.readthedocs.io/en/latest/getting_started.html
TAGGIT_CASE_INSENSITIVE = True


# Simple history
SIMPLE_HISTORY_HISTORY_ID_USE_UUID = True


# CACHING
# https://docs.djangoproject.com/en/2.2/topics/cache/
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '10.0.2.2:11211',
        'OPTIONS': {
            'server_max_value_length': 1024 * 1024 * 2,
        },
        'KEY_PREFIX': 'meteora_cache'
    }
}
