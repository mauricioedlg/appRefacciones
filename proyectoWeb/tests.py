import os
from pathlib import Path
import runpy
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings


class CloudConfigurationTests(SimpleTestCase):
    def load_config(self, **environment):
        with patch.dict(os.environ, environment, clear=True), patch('dotenv.load_dotenv'):
            return runpy.run_path(str(Path(__file__).with_name('settings.py')))

    def test_neon_url_preserves_encoded_password_and_pooler_options(self):
        config = self.load_config(
            DATABASE_URL='postgresql://owner:p%40ss%3A%2F%23%24@ep-demo-pooler.neon.tech/neondb?channel_binding=require',
        )
        database = config['DATABASES']['default']
        self.assertEqual(database['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(database['PASSWORD'], 'p@ss:/#$')
        self.assertEqual(database['OPTIONS']['sslmode'], 'require')
        self.assertEqual(database['OPTIONS']['channel_binding'], 'require')
        self.assertTrue(database['DISABLE_SERVER_SIDE_CURSORS'])
        self.assertTrue(database['CONN_HEALTH_CHECKS'])

    def test_stricter_tls_verification_is_preserved(self):
        config = self.load_config(DATABASE_URL='postgresql://owner:test@host/db?sslmode=verify-full')
        self.assertEqual(config['DATABASES']['default']['OPTIONS']['sslmode'], 'verify-full')

    def test_insecure_postgres_connection_is_rejected(self):
        with self.assertRaisesMessage(ImproperlyConfigured, 'requiere sslmode'):
            self.load_config(DATABASE_URL='postgresql://owner:test@host/db?sslmode=disable')

    def test_non_postgres_url_is_rejected(self):
        with self.assertRaisesMessage(ImproperlyConfigured, 'PostgreSQL para Neon'):
            self.load_config(DATABASE_URL='sqlite:///:memory:')

    def test_render_defaults_to_production_and_uses_assigned_hostname(self):
        config = self.load_config(
            RENDER='true',
            RENDER_EXTERNAL_HOSTNAME='refacciones.onrender.com',
            SECRET_KEY='a-test-key-used-only-to-load-configuration',
            DATABASE_URL='postgresql://owner:test@host/db',
            TRUST_PROXY_HEADERS='True',
        )
        self.assertFalse(config['DEBUG'])
        self.assertEqual(config['ALLOWED_HOSTS'], ['refacciones.onrender.com'])
        self.assertEqual(config['CSRF_TRUSTED_ORIGINS'], ['https://refacciones.onrender.com'])
        self.assertTrue(config['SESSION_COOKIE_SECURE'])
        self.assertTrue(config['SECURE_SSL_REDIRECT'])
        self.assertEqual(config['SECURE_PROXY_SSL_HEADER'], ('HTTP_X_FORWARDED_PROTO', 'https'))

    def test_production_requires_stable_secret_and_database(self):
        with self.assertRaisesMessage(ImproperlyConfigured, 'SECRET_KEY estable'):
            self.load_config(DJANGO_DEBUG='False')
        with self.assertRaisesMessage(ImproperlyConfigured, 'DATABASE_URL'):
            self.load_config(DJANGO_DEBUG='False', SECRET_KEY='test', ALLOWED_HOSTS='example.com')

    def test_local_sql_server_connection_remains_available(self):
        config = self.load_config(DJANGO_DEBUG='True')
        self.assertEqual(config['DATABASES']['default']['ENGINE'], 'mssql')


@override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=['testserver'])
class FrontendDeploymentTests(SimpleTestCase):
    def test_all_pages_render_with_debug_disabled(self):
        for path in Path(__file__).resolve().parent.parent.joinpath('frontend').glob('*.html'):
            with self.subTest(page=path.name):
                response = self.client.get('/' + path.name)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<html')

    def test_home_and_missing_page(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/no_existe.html').status_code, 404)
