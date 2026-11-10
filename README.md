# Aplicación de refacciones

Aplicación Django con pantallas HTML y API en el mismo dominio. La configuración admite PostgreSQL en Neon mediante `DATABASE_URL` y conserva SQL Server para desarrollo local.

La guía completa está en [Conectar Neon y desplegar en Render](docs/neon-render.md). La configuración de despliegue está preparada en el proyecto; crear las cuentas, configurar las credenciales y ejecutar el despliegue son pasos que se realizan en Neon y Render.

## PostgreSQL en Neon

1. Crea un proyecto en [Neon](https://console.neon.tech/) y selecciona su base de datos.
2. En su **SQL Editor**, ejecuta [sql/neon_postgresql.sql](sql/neon_postgresql.sql) completo. En una base vacía crea 7 usuarios, 6 refacciones y 6 notificaciones.
3. En **Connect**, copia la cadena PostgreSQL con `sslmode=require` y guárdala como `DATABASE_URL` en tu archivo privado `.env`.

El script conserva los campos, las relaciones y los ejemplos de `scriptSQL.sql`, y almacena las contraseñas como hashes de Django. Repetirlo conserva los registros existentes. Los registros adicionales que hayas creado en SQL Server requieren una exportación aparte.

En PowerShell, desde la carpeta que contiene `manage.py`:

~~~powershell
if (-not (Test-Path -LiteralPath .venv\Scripts\python.exe)) {
    py -3.13 -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) {
    New-Item -ItemType File -Path .env | Out-Null
}
~~~

El comando crea un `.env` local vacío si todavía no existe. Edita ese archivo con tu `DATABASE_URL`, una `SECRET_KEY` privada y `DJANGO_DEBUG=True` para desarrollo; consulta el [formato y las variables locales](docs/neon-render.md#3-probar-django-desde-windows). Mantén `.env` fuera del repositorio. Después ejecuta:

~~~powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate --fake-initial
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
~~~

Abre [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Con `DATABASE_URL` configurada, esta ejecución local también usa la base de Neon. `--fake-initial` reconoce las tres tablas creadas por el SQL y crea las tablas internas de Django.

## Despliegue en Render

Sube el proyecto a un repositorio y crea un **Blueprint** en Render con [render.yaml](render.yaml). Proporciona `DATABASE_URL` en el formulario privado de Render. El Blueprint genera `SECRET_KEY` y configura `DJANGO_DEBUG=False`; [build.sh](build.sh) instala las dependencias y recopila los estáticos, y [start.sh](start.sh) ejecuta las migraciones y arranca Gunicorn.

La base sigue alojada en Neon. El navegador se comunica con Django mediante las rutas `/api/`; las credenciales PostgreSQL se guardan únicamente en el servidor. Consulta los pasos y las variables de entorno en la [guía Neon y Render](docs/neon-render.md).

La aplicación actual usa la interfaz para identificar al usuario y controlar los roles. Para una publicación de producción con datos reales falta implementar autenticación y permisos en Django. Usa los ejemplos para comprobar el despliegue de demostración.

## Cuentas de demostración

Las primeras seis cuentas usan la contraseña **RefaccionesDemo!26**. La cuenta `mauricio_estrada` conserva **MauricioDemo!26**, según el script original.

| Usuario | Rol | Ejemplo |
| --- | --- | --- |
| solicitante_demo | Solicitante, MBC | Crear solicitudes y consultar sus altas |
| mantenimiento_demo | Gerente de Mantenimiento, MBC | Aprobar `REF-DEMO-001` |
| planta_demo | Gerente de Planta, MBC | Aprobar `REF-DEMO-002` |
| almacen_demo | Almacenista, MBC | Asignar MFG a `REF-DEMO-003` |
| compras_demo | Comprador, MBC | Cotizar `REF-DEMO-004` |
| solicitante_torreon_demo | Solicitante, Torreón | Consultar `REF-DEMO-005` |
| mauricio_estrada | Solicitante, MBC | Crear solicitudes |

Para recorrer el flujo, crea una refacción con `solicitante_demo` y pasa por Mantenimiento, Planta, Almacén y Compras. Cierra sesión al cambiar de rol. Desde **Mis Altas** y **Altas Globales** puedes descargar los registros en Excel.

## Python en VS Code

Abre la carpeta que contiene `manage.py`. [.vscode/settings.json](.vscode/settings.json) apunta a `.venv`.

Si aparecen avisos de imports de Django, presiona **Ctrl+Shift+P**, ejecuta **Python: Select Interpreter** y selecciona `.venv\Scripts\python.exe`. Si persisten los avisos, ejecuta **Developer: Reload Window**.

~~~powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe manage.py check
~~~

## SQL Server local opcional

Para seguir usando la base anterior, instala también sus dependencias:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-sqlserver.txt
~~~

Deja `DATABASE_URL` vacía y `DJANGO_DEBUG=True` en el entorno local. La configuración conserva `RefaccionesLocal` y la instancia `LAPTOPMAU\SQLEXPRESS`, con autenticación de Windows. Puedes cambiar la instancia mediante `REFACCIONES_SQL_SERVER` y el controlador mediante `REFACCIONES_ODBC_DRIVER`.

Ejecuta el `scriptSQL.sql` original en SSMS si necesitas inicializar SQL Server y después ejecuta `manage.py migrate --fake-initial` con ese entorno. PostgreSQL usa el archivo de la carpeta `sql/`.
