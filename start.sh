#!/usr/bin/env bash
set -euo pipefail

# También reconoce las tres tablas si se crearon antes desde el SQL Editor de Neon.
python manage.py migrate --fake-initial --noinput
exec gunicorn proyectoWeb.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}" --access-logfile - --error-logfile -
