import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env', override=False)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    if value.lower().strip() in {'true', '1', 'yes'}:
        return True
    if value.lower().strip() in {'false', '0', 'no'}:
        return False
    raise ImproperlyConfigured(f'{name} debe ser True o False.')


def env_list(name, default=''):
    return [value.strip() for value in os.environ.get(name, default).split(',') if value.strip()]


DEBUG = env_bool('DJANGO_DEBUG', default=os.environ.get('RENDER') != 'true')
SECRET_KEY = os.environ.get('SECRET_KEY') or os.environ.get('REFACCIONES_SECRET_KEY')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('Configura una SECRET_KEY estable antes de desplegar.')
    SECRET_KEY = get_random_secret_key()

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '127.0.0.1,localhost' if DEBUG else '')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')
if render_hostname := os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(render_hostname)
    CSRF_TRUSTED_ORIGINS.append(f'https://{render_hostname}')
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured('Configura ALLOWED_HOSTS con el dominio del despliegue.')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'usuarios',
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

ROOT_URLCONF = 'proyectoWeb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'proyectoWeb.wsgi.application'

# DATABASE_URL se configura en .env local o como secreto en Render.
if database_url := os.environ.get('DATABASE_URL', '').strip():
    try:
        database = dj_database_url.parse(database_url, conn_max_age=60, conn_health_checks=True)
    except (ValueError, KeyError):
        raise ImproperlyConfigured('DATABASE_URL debe ser una URL válida de PostgreSQL.') from None
    if database['ENGINE'] != 'django.db.backends.postgresql':
        raise ImproperlyConfigured('DATABASE_URL debe utilizar PostgreSQL para Neon.')
    # Neon exige TLS; los cursores de servidor no se usan con su pooler.
    database.setdefault('OPTIONS', {}).setdefault('sslmode', 'require')
    if database['OPTIONS']['sslmode'] not in {'require', 'verify-ca', 'verify-full'}:
        raise ImproperlyConfigured('La conexión de Neon requiere sslmode=require o verificación TLS.')
    database['OPTIONS'].setdefault('connect_timeout', 10)
    database['DISABLE_SERVER_SIDE_CURSORS'] = True
    DATABASES = {'default': database}
else:
    if not DEBUG:
        raise ImproperlyConfigured('Configura DATABASE_URL con la conexión de Neon antes de desplegar.')
    # Compatibilidad con la instalación local anterior (requirements-sqlserver.txt).
    sql_server_options = {
        'extra_params': 'Encrypt=yes;TrustServerCertificate=yes',
        'connection_timeout': 5,
    }
    if odbc_driver := os.environ.get('REFACCIONES_ODBC_DRIVER'):
        sql_server_options['driver'] = odbc_driver
    DATABASES = {
        'default': {
            'ENGINE': 'mssql',
            'NAME': 'RefaccionesLocal',
            'HOST': os.environ.get('REFACCIONES_SQL_SERVER', r'LAPTOPMAU\SQLEXPRESS'),
            'OPTIONS': sql_server_options,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', default=not DEBUG)
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
if env_bool('TRUST_PROXY_HEADERS'):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
