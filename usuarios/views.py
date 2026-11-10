from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.http import JsonResponse, HttpResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Usuario, Refaccion, Notificacion
from django.db.models import Q 
import json
import pandas as pd

# MAPEO DE SITIOS (Para referencia rápida)
SITIOS_MAP = {0: 'MBC', 1: 'Torreon', 2: 'Celaya'}

# --------------------------------------------------------------------------
# VISTA: Lista de usuarios
# --------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET", "POST"])
def lista_usuarios(request):
    if request.method == 'GET':
        usuarios = Usuario.objects.values(
            'usuario_id', 'username', 'correo', 'nombre', 'apellidos', 'rol',
            'descripcion_rol', 'numero_de_sitio',
        )
        return JsonResponse(list(usuarios), safe=False)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        nuevo_usuario = Usuario.objects.create(
            username=data['username'],
            correo=data['correo'],
            contrasena=make_password(data['contrasena']),
            nombre=data['nombre'],
            apellidos=data['apellidos'],
            rol=data['rol'],
            descripcion_rol=data.get('descripcion_rol', ''),
            numero_de_sitio=data['numero_de_sitio']
        )
        return JsonResponse({'mensaje': 'Usuario creado correctamente', 'id': nuevo_usuario.usuario_id}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# --------------------------------------------------------------------------
# VISTA: Login
# --------------------------------------------------------------------------
def contrasena_correcta(usuario, contrasena):
    almacenada = usuario.contrasena
    try:
        identify_hasher(almacenada)
    except ValueError:
        # Convierte el formato anterior al iniciar sesión con la contraseña correcta.
        if not constant_time_compare(almacenada, contrasena):
            return False
        Usuario.objects.filter(pk=usuario.pk, contrasena=almacenada).update(
            contrasena=make_password(contrasena),
        )
        return True
    return check_password(contrasena, almacenada)


@csrf_exempt
@require_http_methods(["POST"])
def login_usuario(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = data.get('username')
        contrasena = data.get('contrasena')
        if not isinstance(username, str) or not isinstance(contrasena, str):
            return JsonResponse({'error': 'Credenciales incorrectas'}, status=401)

        for usuario in Usuario.objects.filter(username=username).order_by('pk'):
            if not contrasena_correcta(usuario, contrasena):
                continue
            return JsonResponse({
                'mensaje': 'Login exitoso',
                'nombre': usuario.nombre,
                'usuarioId': usuario.usuario_id,
                'rol': usuario.rol,
                'descripcion_rol': usuario.descripcion_rol,
                'numero_de_sitio': usuario.numero_de_sitio
            }, status=200)
        return JsonResponse({'error': 'Credenciales incorrectas'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# --------------------------------------------------------------------------
# VISTA: Crear Refacción (INICIA FLUJO POR SITIO)
# --------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["POST"])
def crear_refaccion(request):
    try:
        data = request.POST
        usuario_id = data.get('usuario_id')
        archivo = request.FILES.get('archivo_pdf')

        if not usuario_id:
            return JsonResponse({'error': 'usuario_id es requerido'}, status=400)

        # Obtenemos usuario para saber su SITIO
        try:
            solicitante = Usuario.objects.get(usuario_id=usuario_id)
        except Usuario.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)

        sitio_id = solicitante.numero_de_sitio
        nombre_solicitante = f"{solicitante.nombre} {solicitante.apellidos}"

        contenido_pdf = None
        if data.get('familia') == 'Quimicos' and archivo:
            contenido_pdf = archivo.read()

        nueva_refaccion = Refaccion.objects.create(
            descripcion=data.get('descripcion'),
            costo=data.get('costo') if data.get('costo') else None,
            area=data.get('area'),
            consumo=data.get('consumo'),
            frecuencia=data.get('frecuencia'),
            unidad=data.get('unidad'),
            cantidad=data.get('cantidad') if data.get('cantidad') else None,
            observacion=data.get('observacion'),
            numero_parte_proveedor=data.get('numero_parte_proveedor'),
            marca_proveedor=data.get('marca_proveedor'),
            equipos_a_usar=data.get('equipos_a_usar'),
            familia=data.get('familia'),
            reemplazable=data.get('reemplazable'),
            reduce_velocidad=data.get('reduce_velocidad'),
            existe_riesgo=data.get('existe_riesgo'),
            nacionalidad=data.get('nacionalidad'),
            pagina_web=data.get('pagina_web'),
            archivo_pdf=contenido_pdf,
            usuario_id=usuario_id,
            
            # Status Iniciales
            aprobacion_mtto='PENDIENTE',
            aprobacion_planta='PENDIENTE',
            numero_mfg='PENDIENTE',
            cotizado='PENDIENTE' # Nuevo campo
        )

        # NOTIFICAR: Solo a Gerentes de Mantenimiento del MISMO SITIO
        gerentes = Usuario.objects.filter(
            descripcion_rol='Gerente Mantenimiento',
            numero_de_sitio=sitio_id
        )

        for gerente in gerentes:
            Notificacion.objects.create(
                usuario=gerente,
                mensaje=f"Nuevo registro en {SITIOS_MAP.get(sitio_id, 'Sitio'+str(sitio_id))} de: {nombre_solicitante}. Ref: {nueva_refaccion.descripcion}",
                url_destino="aprobaciones_pendientes.html"
            )

        return JsonResponse({'mensaje': 'Refacción creada', 'id': nueva_refaccion.id}, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# --------------------------------------------------------------------------
# VISTAS: Consultas (Mis Refacciones / Todas)
# --------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET"])
def mis_refacciones(request, usuario_id):
    try:
        refacciones = list(Refaccion.objects.filter(usuario_id=usuario_id).values())
        for ref in refacciones:
            if 'archivo_pdf' in ref: del ref['archivo_pdf']
            if 'foto_refaccion' in ref: del ref['foto_refaccion']
        return JsonResponse(refacciones, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def todas_refacciones(request):
    try:
        refacciones = list(Refaccion.objects.all().values())
        
        # Enriquecer datos para filtros globales
        for ref in refacciones:
            if 'archivo_pdf' in ref: del ref['archivo_pdf']
            if 'foto_refaccion' in ref: del ref['foto_refaccion']
            
            try:
                usr = Usuario.objects.get(usuario_id=ref['usuario_id'])
                # Agregar nombre solicitante
                ref['nombre_solicitante'] = f"{usr.nombre} {usr.apellidos}"
                # Agregar nombre del sitio usando el MAP
                ref['nombre_sitio'] = SITIOS_MAP.get(usr.numero_de_sitio, 'Desconocido')
            except Usuario.DoesNotExist:
                ref['nombre_solicitante'] = "Usuario Eliminado"
                ref['nombre_sitio'] = "N/A"

        return JsonResponse(refacciones, safe=False, status=200)
    except Exception as e:
         return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def descargar_excel(request, usuario_id):
    try:
        refacciones = list(Refaccion.objects.filter(usuario_id=usuario_id).values())
        if not refacciones:
            return JsonResponse({'error': 'No hay datos para exportar'}, status=404)
        for ref in refacciones:
            if 'archivo_pdf' in ref: del ref['archivo_pdf']
            if 'foto_refaccion' in ref: del ref['foto_refaccion']
        df = pd.DataFrame(refacciones)
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="mis_refacciones.xlsx"'
        df.to_excel(response, index=False, engine='openpyxl')
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def descargar_excel_global(request):
    try:
        refacciones = list(Refaccion.objects.all().values())
        if not refacciones:
            return JsonResponse({'error': 'No hay datos para exportar'}, status=404)
        for ref in refacciones:
            if 'archivo_pdf' in ref: del ref['archivo_pdf']
            if 'foto_refaccion' in ref: del ref['foto_refaccion']
        df = pd.DataFrame(refacciones)
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="todas_refacciones.xlsx"'
        df.to_excel(response, index=False, engine='openpyxl')
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def detalle_refaccion(request, refaccion_id):
    if request.method == 'GET':
        try:
            data = Refaccion.objects.filter(id=refaccion_id).values().first()
            if not data:
                return JsonResponse({'error': 'Refacción no encontrada'}, status=404)
            
            if 'archivo_pdf' in data: del data['archivo_pdf'] 
            if 'foto_refaccion' in data: del data['foto_refaccion']

            try:
                usuario = Usuario.objects.get(usuario_id=data['usuario_id'])
                data['nombre_solicitante'] = f"{usuario.nombre} {usuario.apellidos}"
            except Usuario.DoesNotExist:
                data['nombre_solicitante'] = "Usuario Desconocido"
            return JsonResponse(data, safe=False, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    if request.method == 'POST':
        try:
            refaccion = Refaccion.objects.filter(id=refaccion_id).first()
            if not refaccion:
                return JsonResponse({'error': 'Refacción no encontrada'}, status=404)
            data = request.POST
            archivo = request.FILES.get('archivo_pdf')

            # Actualización de campos
            refaccion.descripcion = data.get('descripcion', refaccion.descripcion)
            if 'costo' in data:
                refaccion.costo = data.get('costo') or None
            refaccion.area = data.get('area', refaccion.area)
            refaccion.consumo = data.get('consumo', refaccion.consumo)
            refaccion.frecuencia = data.get('frecuencia', refaccion.frecuencia)
            refaccion.unidad = data.get('unidad', refaccion.unidad)
            if 'cantidad' in data:
                refaccion.cantidad = data.get('cantidad') or None
            refaccion.observacion = data.get('observacion', refaccion.observacion)
            refaccion.numero_parte_proveedor = data.get('numero_parte_proveedor', refaccion.numero_parte_proveedor)
            refaccion.marca_proveedor = data.get('marca_proveedor', refaccion.marca_proveedor)
            refaccion.equipos_a_usar = data.get('equipos_a_usar', refaccion.equipos_a_usar)
            refaccion.familia = data.get('familia', refaccion.familia)
            refaccion.reemplazable = data.get('reemplazable', refaccion.reemplazable)
            refaccion.reduce_velocidad = data.get('reduce_velocidad', refaccion.reduce_velocidad)
            refaccion.existe_riesgo = data.get('existe_riesgo', refaccion.existe_riesgo)
            refaccion.nacionalidad = data.get('nacionalidad', refaccion.nacionalidad)
            refaccion.pagina_web = data.get('pagina_web', refaccion.pagina_web)

            if refaccion.familia == 'Quimicos' and archivo:
                refaccion.archivo_pdf = archivo.read()
            elif refaccion.familia != 'Quimicos':
                refaccion.archivo_pdf = None

            refaccion.save()
            return JsonResponse({'mensaje': 'Refacción actualizada correctamente'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

# --------------------------------------------------------------------------
# VISTAS: Aprobación MANTENIMIENTO
# --------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET"])
def pendientes_aprobacion(request):
    try:
        refs_qs = Refaccion.objects.filter(aprobacion_mtto='PENDIENTE').select_related('usuario')
        lista_final = []
        for r in refs_qs:
            lista_final.append({
                'id': r.id,
                'descripcion': r.descripcion,
                'usuario_id': r.usuario_id,
                'nombre_solicitante': f"{r.usuario.nombre} {r.usuario.apellidos}",
                'aprobacion_mtto': r.aprobacion_mtto
            })
        return JsonResponse(lista_final, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def gestionar_aprobacion(request, refaccion_id):
    try:
        data = json.loads(request.body.decode('utf-8'))
        accion = data.get('accion') 

        refaccion = Refaccion.objects.select_related('usuario').filter(id=refaccion_id).first()
        if not refaccion:
            return JsonResponse({'error': 'Refacción no encontrada'}, status=404)

        refaccion.aprobacion_mtto = accion
        refaccion.save()

        # Determinar SITIO del dueño de la refacción
        sitio_id = refaccion.usuario.numero_de_sitio

        if accion == 'SI':
             # Notificar solo a Gerentes de Planta del MISMO SITIO
             gerentes_planta = Usuario.objects.filter(
                 descripcion_rol='Gerente Planta',
                 numero_de_sitio=sitio_id
             )
             for gp in gerentes_planta:
                 Notificacion.objects.create(
                     usuario=gp,
                     mensaje=f"Mtto Aprobado. Pendiente revisión Planta: {refaccion.descripcion}",
                     url_destino="aprobaciones_pendientes.html"
                 )
        else:
             Notificacion.objects.create(
                usuario=refaccion.usuario,
                mensaje=f"Tu refacción '{refaccion.descripcion}' fue RECHAZADA por Mantenimiento.",
                url_destino="mis_altas.html"
             )

        return JsonResponse({'mensaje': f'Mantenimiento: Refacción {accion}'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# --------------------------------------------------------------------------
# VISTAS: Aprobación PLANTA
# --------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET"])
def pendientes_aprobacion_planta(request):
    try:
        refs_qs = Refaccion.objects.filter(aprobacion_mtto='SI', aprobacion_planta='PENDIENTE').select_related('usuario')
        lista_final = []
        for r in refs_qs:
            lista_final.append({
                'id': r.id,
                'descripcion': r.descripcion,
                'usuario_id': r.usuario_id,
                'nombre_solicitante': f"{r.usuario.nombre} {r.usuario.apellidos}",
                'aprobacion_mtto': r.aprobacion_mtto,
                'aprobacion_planta': r.aprobacion_planta
            })
        return JsonResponse(lista_final, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def gestionar_aprobacion_planta(request, refaccion_id):
    try:
        data = json.loads(request.body.decode('utf-8'))
        accion = data.get('accion') 

        refaccion = Refaccion.objects.select_related('usuario').filter(id=refaccion_id).first()
        if not refaccion:
            return JsonResponse({'error': 'Refacción no encontrada'}, status=404)

        refaccion.aprobacion_planta = accion
        refaccion.save()

        sitio_id = refaccion.usuario.numero_de_sitio

        if accion == 'SI':
            # Notificar solo a Almacenistas del MISMO SITIO
            almacenistas = Usuario.objects.filter(
                descripcion_rol='Almacenista',
                numero_de_sitio=sitio_id
            )
            for alm in almacenistas:
                Notificacion.objects.create(
                    usuario=alm,
                    mensaje=f"Planta Aprobó. Pendiente MFG: {refaccion.descripcion}",
                    url_destino="asignacion_mfg.html"
                )
            
            Notificacion.objects.create(
                usuario=refaccion.usuario,
                mensaje=f"Planta aprobó '{refaccion.descripcion}'. Pendiente asignación MFG.",
                url_destino="mis_altas.html"
            )
        else:
            Notificacion.objects.create(
                usuario=refaccion.usuario,
                mensaje=f"Planta RECHAZÓ tu refacción '{refaccion.descripcion}'.",
                url_destino="mis_altas.html"
            )

        return JsonResponse({'mensaje': f'Planta: Refacción {accion}'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# --------------------------------------------------------------------------
# VISTAS: Almacenista (Asignar MFG)
# --------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET"])
def pendientes_asignacion_mfg(request):
    try:
        refs_qs = Refaccion.objects.filter(
            aprobacion_planta='SI', 
            numero_mfg='PENDIENTE'
        ).select_related('usuario')
        
        lista_final = []
        for r in refs_qs:
            lista_final.append({
                'id': r.id,
                'descripcion': r.descripcion,
                'nombre_solicitante': f"{r.usuario.nombre} {r.usuario.apellidos}",
                'numero_parte_proveedor': r.numero_parte_proveedor,
                'aprobacion_planta': r.aprobacion_planta
            })
        return JsonResponse(lista_final, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def asignar_mfg(request, refaccion_id):
    try:
        data = json.loads(request.body.decode('utf-8'))
        mfg = data.get('numero_mfg') 

        if not mfg:
            return JsonResponse({'error': 'El numero MFG es obligatorio'}, status=400)

        refaccion = Refaccion.objects.select_related('usuario').filter(id=refaccion_id).first()
        if not refaccion:
            return JsonResponse({'error': 'Refacción no encontrada'}, status=404)

        refaccion.numero_mfg = mfg
        refaccion.save()

        sitio_id = refaccion.usuario.numero_de_sitio

        # 1. Notificar al USUARIO (Dueño)
        Notificacion.objects.create(
            usuario=refaccion.usuario,
            mensaje=f"PROCESO COMPLETADO. '{refaccion.descripcion}' tiene MFG: {mfg}",
            url_destino="mis_altas.html"
        )
        
        # 2. Notificar al COMPRADOR del MISMO SITIO
        compradores = Usuario.objects.filter(
            descripcion_rol='Comprador',
            numero_de_sitio=sitio_id
        )
        for comp in compradores:
            Notificacion.objects.create(
                usuario=comp,
                mensaje=f"Pendiente de Cotizar: '{refaccion.descripcion}' (MFG Asignado)",
                url_destino="cotizaciones_pendientes.html"
            )

        return JsonResponse({'mensaje': 'Número MFG asignado y Comprador notificado'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# --------------------------------------------------------------------------
# VISTAS: Notificaciones
# --------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(["GET"])
def obtener_notificaciones(request, usuario_id):
    try:
        notifs = list(Notificacion.objects.filter(usuario_id=usuario_id)
                      .order_by('leido', '-fecha').values())
        return JsonResponse(notifs, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def leer_notificacion(request, notificacion_id):
    try:
        n = Notificacion.objects.get(id=notificacion_id)
        n.leido = True
        n.save()
        return JsonResponse({'mensaje': 'Leido'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# --------------------------------------------------------------------------
# VISTAS: Requerimiento Fotos y Tabla MFG (Almacenista 2)
# --------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["GET"])
def refacciones_con_mfg(request):
    try:
        refacciones = list(Refaccion.objects.exclude(numero_mfg='PENDIENTE').values())
        
        for ref in refacciones:
            if 'archivo_pdf' in ref: del ref['archivo_pdf']
            if 'foto_refaccion' in ref: del ref['foto_refaccion']
            
            try:
                usr = Usuario.objects.get(usuario_id=ref['usuario_id'])
                ref['nombre_solicitante'] = f"{usr.nombre} {usr.apellidos}"
            except:
                ref['nombre_solicitante'] = "Desconocido"

        return JsonResponse(refacciones, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def subir_foto(request, refaccion_id):
    try:
        refaccion = Refaccion.objects.filter(id=refaccion_id).first()
        if not refaccion:
            return JsonResponse({'error': 'No existe la refaccion'}, status=404)
            
        foto = request.FILES.get('foto')
        if not foto:
            return JsonResponse({'error': 'No se envió ninguna imagen'}, status=400)
            
        refaccion.foto_refaccion = foto.read()
        refaccion.save()
        
        return JsonResponse({'mensaje': 'Foto subida correctamente'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def ver_foto(request, refaccion_id):
    try:
        ref = Refaccion.objects.filter(id=refaccion_id).first()
        if not ref or not ref.foto_refaccion:
            return HttpResponse(status=404) 
        return HttpResponse(ref.foto_refaccion, content_type="image/jpeg")
    except Exception as e:
        return HttpResponse(status=400)

@csrf_exempt
@require_http_methods(["GET"])
def descargar_pdf(request, refaccion_id):
    try:
        ref = Refaccion.objects.filter(id=refaccion_id).first()
        if not ref or not ref.archivo_pdf:
             return HttpResponse("No hay PDF disponible", status=404)

        response = HttpResponse(ref.archivo_pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ficha_tecnica_{refaccion_id}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(str(e), status=400)

# --------------------------------------------------------------------------
# VISTAS: ROL COMPRADOR (Nuevos Requerimientos)
# --------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["GET"])
def pendientes_cotizacion(request):
    try:
        # Filtro: Ya tiene MFG asignado, pero Cotizado sigue PENDIENTE
        refs_qs = Refaccion.objects.filter(
            cotizado='PENDIENTE'
        ).exclude(numero_mfg='PENDIENTE').select_related('usuario')
        
        lista_final = []
        for r in refs_qs:
            lista_final.append({
                'id': r.id,
                'descripcion': r.descripcion,
                'numero_mfg': r.numero_mfg,
                'nombre_solicitante': f"{r.usuario.nombre} {r.usuario.apellidos}",
                'numero_parte_proveedor': r.numero_parte_proveedor
            })
        return JsonResponse(lista_final, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def realizar_cotizacion(request, refaccion_id):
    try:
        refaccion = Refaccion.objects.filter(id=refaccion_id).first()
        if not refaccion:
            return JsonResponse({'error': 'Refacción no encontrada'}, status=404)

        refaccion.cotizado = 'SI'
        refaccion.save()

        # Notificar al dueño de la refacción
        Notificacion.objects.create(
            usuario=refaccion.usuario,
            mensaje=f"Tu solicitud '{refaccion.descripcion}' ha sido COTIZADA.",
            url_destino="mis_altas.html"
        )

        return JsonResponse({'mensaje': 'Cotización concluida correctamente'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["GET"])
def lista_cotizadas(request):
    try:
        refacciones = list(Refaccion.objects.filter(cotizado='SI').values())
        
        for ref in refacciones:
            if 'archivo_pdf' in ref: del ref['archivo_pdf']
            if 'foto_refaccion' in ref: del ref['foto_refaccion']
            
            try:
                usr = Usuario.objects.get(usuario_id=ref['usuario_id'])
                ref['nombre_solicitante'] = f"{usr.nombre} {usr.apellidos}"
            except:
                ref['nombre_solicitante'] = "Desconocido"

        return JsonResponse(refacciones, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
