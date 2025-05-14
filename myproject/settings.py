import os
from pathlib import Path
from dotenv import load_dotenv
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from django.db import IntegrityError

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


load_dotenv(BASE_DIR / '.env')

SECRET_KEY = 'django-insecure-your-secret-key-here'

DEBUG = False  # Было True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myproject.apps.MyprojectConfig',
    'rest_framework',
    'drf_yasg',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'myproject.middleware.ErrorHandlingMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'myproject' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': False,
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'myproject.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки авторизации
LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

# Настройки Swagger
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Basic': {
            'type': 'basic'
        }
    },
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEFAULT_MODEL_RENDERING': 'model',
    'DEFAULT_INFO': {
        'contact': {
            'name': 'API Support',
            'url': 'http://localhost:8000/',
            'email': 'support@example.com'
        },
        'license': {},
        'version': '1.0.0',
        'title': 'API Documentation',
        'description': 'API documentation for the job portal'
    }
}

# REST Framework settings
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'myproject.utils.error_handler.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'UNAUTHENTICATED_USER': None,
    'NON_FIELD_ERRORS_KEY': 'error',
    'AUTHENTICATION_FAILED_HANDLER': 'myproject.utils.error_handler.custom_authentication_failed_handler',
}

# Показывать кастомные страницы ошибок даже в режиме отладки
DEBUG_PROPAGATE_EXCEPTIONS = True

# Настройки для Yandex Object Storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


AWS_ACCESS_KEY_ID = os.environ.get('YC_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('YC_SECRET_ACCESS_KEY')

AWS_STORAGE_BUCKET_NAME = 'urfu-vacancies'  # Имя вашего бакета
AWS_S3_ENDPOINT_URL = 'https://storage.yandexcloud.net'
AWS_S3_REGION_NAME = 'ru-central1' # Например, 'ru-central1'
AWS_S3_FILE_OVERWRITE = False  # Не перезаписывать файлы по умолчанию
AWS_DEFAULT_ACL = 'public-read'  # Делать файлы публично доступными для чтения
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400', # Контроль кэширования (1 день)
}
AWS_LOCATION = 'static' # Папка внутри бакета для статических файлов
STATIC_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{AWS_LOCATION}/'

# Если вы также хотите хранить медиафайлы (загружаемые пользователями) в Object Storage:
# MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/media/' # Папка для медиафайлов
# MEDIA_ROOT = MEDIA_URL # Для django-storages это не путь к файловой системе
