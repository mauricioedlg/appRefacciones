from django.contrib import admin
from django.urls import path, re_path
from .views import pagina_frontend
from usuarios import views

urlpatterns = [
    path('', pagina_frontend),
    re_path(
        r'^(?P<pagina>[a-z_]+\.html)$',
        pagina_frontend,
    ),
    path('admin/', admin.site.urls),
    path('api/usuarios/', views.lista_usuarios),
    path('api/login/', views.login_usuario),
    path('api/refacciones/', views.crear_refaccion),
    path('api/mis_refacciones/<int:usuario_id>/', views.mis_refacciones),
    path('api/descargar_excel/<int:usuario_id>/', views.descargar_excel),
    path('api/refaccion/<int:refaccion_id>/', views.detalle_refaccion),
    path('api/todas_refacciones/', views.todas_refacciones),
    path('api/descargar_excel_global/', views.descargar_excel_global),

    # APROBACIONES
    path('api/pendientes_aprobacion/', views.pendientes_aprobacion),
    path('api/gestionar_aprobacion/<int:refaccion_id>/', views.gestionar_aprobacion),
    path('api/pendientes_aprobacion_planta/', views.pendientes_aprobacion_planta),
    path('api/gestionar_aprobacion_planta/<int:refaccion_id>/', views.gestionar_aprobacion_planta),

    # ALMACEN
    path('api/pendientes_asignacion_mfg/', views.pendientes_asignacion_mfg),
    path('api/asignar_mfg/<int:refaccion_id>/', views.asignar_mfg),

    # NOTIFICACIONES
    path('api/notificaciones/<int:usuario_id>/', views.obtener_notificaciones),
    path('api/notificaciones/leer/<int:notificacion_id>/', views.leer_notificacion),

    # --- NUEVAS RUTAS (REQ. FOTO Y TABLA MFG) ---
    path('api/refacciones_con_mfg/', views.refacciones_con_mfg), # Tabla filtrada
    path('api/subir_foto/<int:refaccion_id>/', views.subir_foto),
    path('api/ver_foto/<int:refaccion_id>/', views.ver_foto),
    path('api/descargar_pdf/<int:refaccion_id>/', views.descargar_pdf), # Descargar PDF Quimico


    # --- NUEVAS RUTAS COMPRADOR ---
    path('api/pendientes_cotizacion/', views.pendientes_cotizacion),
    path('api/realizar_cotizacion/<int:refaccion_id>/', views.realizar_cotizacion),
    path('api/lista_cotizadas/', views.lista_cotizadas),

]
