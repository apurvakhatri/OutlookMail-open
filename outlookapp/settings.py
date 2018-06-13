"""
Django settings for outlookapp project.

Generated by 'django-admin startproject' using Django 2.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import json

data = open('yellowant_app_credentials.json').read()
data_json = json.loads(data)
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'doq%!&koou%fd7l#)w@4gai-xw%s+gvl&m^^8us(l-h6hoxjbo'

# SECURITY WARNING: don't run with debug turned on in production!
app_name = os.environ.get("HEROKU_APP_NAME")
BASE_URL = "https://{}.herokuapp.com".format(app_name)
ALLOWED_HOSTS = ['*', '{}.herokuapp.com'.format(app_name)]

DEBUG = True


BASE_HREF = "/"
SITE_PROTOCOL = "http://"


DEV_ENV = os.environ.get('ENV', 'DEV')
if DEV_ENV=="DEV":
    OUTLOOK_CLIENT_ID = "f5fa45b4-0498-4ea4-9774-201deb5ffe77"
    OUTLOOK_CLIENT_SECRET = "scmgtTFJ2}zgJQTN3459{#)"
    BASE_URL = "https://c6bb6ead.ngrok.io/"
    SITE_DOMAIN_URL = "ngrok.io"
elif DEV_ENV=="HEROKU":
    BASE_URL = "https://{}.herokuapp.com/".format(app_name)
    OUTLOOK_CLIENT_ID = os.environ.get('OM_CLIENT_ID')
    OUTLOOK_CLIENT_SECRET = os.environ.get('OM_CLIENT_SECRET')
    app_name = os.environ.get("HEROKU_APP_NAME")
    SITE_DOMAIN_URL = "herokuapp.com"

OUTLOOK_REDIRECT_URL = BASE_URL + "outlookauthurl/"
OUTLOOK_REDIRECT = BASE_URL + "outlookredirecttoken/"

YA_OAUTH_URL = "https://www.yellowant.com/api/oauth2/authorize/"
#YA_APP_ID defined
YA_APP_ID = str(data_json['application_id'])

YA_CLIENT_ID = str(data_json['client_id'])
YA_CLIENT_SECRET = str(data_json['client_secret'])
YA_VERIFICATION_TOKEN = str(data_json['verification_token'])
YA_REDIRECT_URL = BASE_URL + "redirecturl/"
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'lib.records',
    'lib.web'
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
]

ROOT_URLCONF = 'outlookapp.urls'

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

WSGI_APPLICATION = 'outlookapp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'outlookmailapp1',
        'USER': 'root',
        'PASSWORD': 'khatri@19',
        'HOST': 'localhost',
        'PORT': '',
    }
}
if DEV_ENV=="HEROKU":
    import dj_database_url
    db_from_env = dj_database_url.config()
    DATABASES['default'].update(db_from_env)
    DATABASES['default']['CONN_MAX_AGE'] = 500

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

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
