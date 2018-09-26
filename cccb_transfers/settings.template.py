"""
Django settings for cccb_transfers project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '1+ctigmygs**gkf5b#2g*a3ff)h$8tfkb2%oq&q@d41e&et6=p'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['{{domain}}', ]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'django_filters',
    'transfer_app.apps.TransferAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cccb_transfers.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),],
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

WSGI_APPLICATION = 'cccb_transfers.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

# Settings specific to REST framework:
REST_FRAMEWORK = {

    # At minimum, we don't allow any unauthenticated access.
    # Specific views may have admin- or user-specific privileges
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',)
}


####################
# Configuration for Sites framework:
SITE_ID = 1


# some identifiers for consistent reference:
GOOGLE = 'google'
AWS = 'aws'
GOOGLE_DRIVE = 'google_drive'
DROPBOX = 'dropbox'

####################

# Read the general configuration file, which will load the settings appropriate for the environment
import cccb_transfers.utils as utils

additional_sections = [GOOGLE_DRIVE, DROPBOX]
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
CONFIG_PARAMS = utils.read_general_config(os.path.join(CONFIG_DIR, 'general.cfg'), additional_sections)

additional_sections = [GOOGLE_DRIVE, DROPBOX, GOOGLE]
LIVE_TEST_CONFIG_PARAMS = utils.read_config(os.path.join(CONFIG_DIR, 'live_tests.cfg'), additional_sections)

###################
# Configuration for upload providers and compute environments:

UPLOADER_CONFIG = {
    'CONFIG_PATH' : os.path.join(CONFIG_DIR, 'uploaders.cfg'),

    # for each item in the following dictionary, there needs to be a section 
    # header in the config file located at UPLOADER_CONFIG.CONFIG_PATH
    'UPLOAD_SOURCES' : [
        DROPBOX,
        GOOGLE_DRIVE
    ]
}

DOWNLOADER_CONFIG = {
    'CONFIG_PATH' : os.path.join(CONFIG_DIR, 'downloaders.cfg'),

    # for each item in the following dictionary, there needs to be a section 
    # header in the config file located at UPLOADER_CONFIG.CONFIG_PATH
    'DOWNLOAD_DESTINATIONS' : [
        DROPBOX,
        GOOGLE_DRIVE
    ]
}

LOGIN_URL = '/login/'

#Celery settings:
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'