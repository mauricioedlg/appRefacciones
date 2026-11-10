# Conectar Neon y desplegar en Render

El proyecto usa Django para servir las pantallas y la API. Neon aloja PostgreSQL; Render ejecuta Django. La conexión a la base se configura con `DATABASE_URL` y permanece en el servidor.

Esta guía prepara un despliegue de demostración. La identidad y los roles de la aplicación todavía se controlan desde la interfaz: antes de publicar un servicio de producción con datos reales, implementa autenticación y autorización en las rutas de Django.

## 1. Crear el proyecto en Neon

Entra a [la consola de Neon](https://console.neon.tech/) y crea un proyecto, por ejemplo `refacciones`. Selecciona una región cercana a la que usarás para la aplicación en Render. Conserva la base que crea Neon, o crea otra desde su consola; anota cuál seleccionaste para usarla en los siguientes pasos. La [guía oficial de Neon para Django](https://neon.com/docs/guides/django) explica la creación del proyecto y la conexión con TLS.

Abre **SQL Editor** y selecciona la misma rama y base de datos. Copia el contenido completo de [sql/neon_postgresql.sql](../sql/neon_postgresql.sql) y ejecútalo.

En una base vacía el resultado final debe indicar:

| Tabla | Registros de ejemplo |
| --- | ---: |
| usuarios | 7 |
| refacciones | 6 |
| notificaciones | 6 |

El script crea las tablas de la aplicación, sus relaciones e índices. Usa columnas PostgreSQL compatibles con los modelos de Django y conserva las mayúsculas de nombres como `"UsuarioID"` y `"Correo"`. Puedes ejecutarlo otra vez: inserta los ejemplos faltantes y conserva las cuentas, las contraseñas y el avance de registros existentes. Por ello, una base que ya contiene otros registros puede mostrar conteos mayores.

Este archivo reproduce el esquema y los ejemplos del `scriptSQL.sql` entregado. Si has creado más usuarios, solicitudes, archivos o notificaciones en SQL Server, esos datos necesitan una exportación y transferencia aparte.

## 2. Guardar la conexión privada

En **Connect** de Neon, selecciona la misma rama, base y rol. Copia la cadena de conexión PostgreSQL; para la aplicación puedes usar la opción de conexión agrupada, cuyo host contiene `-pooler`. Conserva los parámetros de seguridad, incluido `sslmode=require`.

Guarda la cadena como `DATABASE_URL` en tu `.env` local y, más adelante, en el formulario privado de variables de Render. No la pegues en el chat, en archivos HTML ni en el repositorio. `.env.example` contiene nombres de variables y ejemplos; `.env` contiene tus valores privados.

La configuración de Django selecciona PostgreSQL cuando existe `DATABASE_URL`. Exige TLS, desactiva los cursores del servidor para trabajar con la conexión agrupada y comprueba las conexiones reutilizadas. Sin esa variable, el modo de desarrollo conserva SQL Server.

## 3. Probar Django desde Windows

Abre PowerShell en la carpeta que contiene `manage.py`. Usa Python 3.13 o 3.12; ajusta el selector del primer comando si usas 3.12:

~~~powershell
if (-not (Test-Path -LiteralPath .venv\Scripts\python.exe)) {
    py -3.13 -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
~~~

El comando de copia conserva un `.env` que ya existe. Edita ese archivo con tus valores:

| Variable | Desarrollo local |
| --- | --- |
| `DATABASE_URL` | Cadena privada de Neon con TLS |
| `DJANGO_DEBUG` | `True` |
| `SECRET_KEY` | Valor aleatorio privado para desarrollo |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` |
| `CSRF_TRUSTED_ORIGINS` | Orígenes locales indicados en `.env.example` |
| `TRUST_PROXY_HEADERS` | `False` |

Puedes generar una clave local con este comando y guardar el resultado en `SECRET_KEY` dentro de `.env`:

~~~powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
~~~

Después de ejecutar el SQL en Neon:

~~~powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate --fake-initial
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
~~~

`--fake-initial` reconoce las tablas de la aplicación que ya existen y permite crear las tablas internas de Django. En una base vacía también puedes ejecutar primero `migrate` y después el SQL para cargar los ejemplos; usa una de estas secuencias para inicializar la base.

Abre [http://127.0.0.1:8000/](http://127.0.0.1:8000/) e inicia sesión con una cuenta de la [tabla de demostración](../README.md#cuentas-de-demostración). Aunque Django se ejecuta en tu equipo, sus consultas ya van a Neon cuando `DATABASE_URL` está configurada.

## 4. Crear el servicio de Render

Sube el contenido de esta carpeta a un repositorio Git al que Render pueda acceder. La raíz del proyecto debe contener `manage.py`, `requirements.txt`, `render.yaml`, `build.sh`, `start.sh`, `proyectoWeb/`, `usuarios/` y `frontend/`. Guarda las credenciales fuera del repositorio.

En Render abre **Blueprints**, crea un Blueprint y selecciona ese repositorio. Usa [render.yaml](../render.yaml), que define el servicio Django y solicita tu `DATABASE_URL`. La [guía oficial de despliegue Django en Render](https://render.com/docs/deploy-django) describe este flujo. Este proyecto conecta con Neon y no necesita crear una segunda base de datos en Render.

Configura estas variables en el servicio:

| Variable | Valor en Render |
| --- | --- |
| `DATABASE_URL` | Cadena privada de Neon, en el campo solicitado por el Blueprint |
| `SECRET_KEY` | La genera el Blueprint; conserva esa clave entre despliegues |
| `DJANGO_DEBUG` | `False` |
| `TRUST_PROXY_HEADERS` | `True`, para reconocer HTTPS detrás del proxy de Render |
| `ALLOWED_HOSTS` | El dominio de Render se incorpora desde `RENDER_EXTERNAL_HOSTNAME`; añade dominios propios si los usas |
| `CSRF_TRUSTED_ORIGINS` | El origen HTTPS de Render también se incorpora automáticamente; añade los orígenes de dominios propios |

Los dominios de `ALLOWED_HOSTS` se escriben sin `https://` ni rutas. Los orígenes de `CSRF_TRUSTED_ORIGINS` incluyen `https://`; usa comas para separar varios valores. Para un dominio propio, configura también el dominio y su certificado en Render.

Si prefieres crear el servicio manualmente, selecciona **Web Service**, el repositorio y el entorno Python. Usa **Build Command** `bash build.sh` y **Start Command** `bash start.sh`, y configura las mismas variables; en ese caso genera tú la `SECRET_KEY` privada desde Render.

Render usa la rama de Python 3.13 definida en `.python-version`. `build.sh` instala las dependencias y ejecuta `collectstatic`. `start.sh` ejecuta `migrate --fake-initial` y arranca Gunicorn con la aplicación WSGI de este proyecto y el puerto asignado por Render. El arranque comprueba las migraciones en cada despliegue y conserva los datos de Neon.

## 5. Comprobar la demostración

Cuando Render termine el despliegue, abre la URL HTTPS del servicio e inicia sesión con `solicitante_demo`. Crea una solicitud de prueba y comprueba que aparece al volver a entrar. Puedes revisar esa fila en el SQL Editor de la misma base de Neon. Así verificas que el navegador, Django y PostgreSQL están conectados.

Las pantallas llaman a rutas relativas `/api/`, por lo que comparten dominio con Django. Las fotos y los PDF usan campos binarios de la base y permanecen en Neon. Los estáticos del administrador se recopilan durante el build y se sirven con WhiteNoise.

Antes de tratar datos reales, completa los controles de acceso del backend y revisa la [guía de despliegue de Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/). En el entorno del servidor puedes ejecutar `python manage.py check --deploy` para revisar la configuración; ese comando no valida los permisos propios de la aplicación.

## Si falla la conexión o el despliegue

Un error de contraseña o de host se revisa copiando de nuevo la cadena de **Connect** en Neon y actualizando `DATABASE_URL` en Render. Comprueba que apunte a la misma base donde ejecutaste el SQL y conserva los parámetros TLS.

Si Django indica que faltan tablas, confirma la base seleccionada y que `migrate --fake-initial` terminó correctamente. Un error `DisallowedHost` se corrige añadiendo el dominio exacto a `ALLOWED_HOSTS`. Para errores CSRF del administrador, revisa los orígenes HTTPS en `CSRF_TRUSTED_ORIGINS` y el reconocimiento del proxy de Render.

Consulta los logs del servicio para identificar el mensaje concreto. Mantén `DJANGO_DEBUG=False` en la nube y comparte únicamente el texto del error que no contenga credenciales.
