from django.db import models
from django.utils import timezone

class Usuario(models.Model):
    usuario_id = models.AutoField(primary_key=True, db_column='UsuarioID')
    username = models.CharField(max_length=50, db_column='Username')
    correo = models.CharField(max_length=100, unique=True, db_column='Correo')
    contrasena = models.CharField(max_length=100, db_column='Contrasena')
    nombre = models.CharField(max_length=100, db_column='Nombre')
    apellidos = models.CharField(max_length=150, db_column='Apellidos')
    rol = models.PositiveSmallIntegerField(db_column='Rol')
    descripcion_rol = models.CharField(max_length=200, null=True, blank=True, db_column='DescripcionRol')
    numero_de_sitio = models.PositiveSmallIntegerField(db_column='NumeroDeSitio')

    class Meta:
        db_table = 'usuarios'

class Refaccion(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    costo = models.FloatField(null=True, blank=True)
    area = models.CharField(max_length=100, null=True, blank=True)
    consumo = models.CharField(max_length=100, null=True, blank=True)
    frecuencia = models.CharField(max_length=100, null=True, blank=True)
    unidad = models.CharField(max_length=50, null=True, blank=True)
    cantidad = models.IntegerField(null=True, blank=True)
    observacion = models.CharField(max_length=255, null=True, blank=True)
    numero_parte_proveedor = models.CharField(max_length=100, unique=True)
    marca_proveedor = models.CharField(max_length=100, null=True, blank=True)
    equipos_a_usar = models.CharField(max_length=255, null=True, blank=True)
    familia = models.CharField(max_length=100, null=True, blank=True)
    reemplazable = models.CharField(max_length=50, null=True, blank=True)
    reduce_velocidad = models.CharField(max_length=50, null=True, blank=True)
    existe_riesgo = models.CharField(max_length=50, null=True, blank=True)
    nacionalidad = models.CharField(max_length=50, null=True, blank=True)
    pagina_web = models.CharField(max_length=255, null=True, blank=True)
    archivo_pdf = models.BinaryField(null=True, blank=True)
    
    aprobacion_mtto = models.CharField(max_length=50, default='PENDIENTE', null=True, blank=True)
    aprobacion_planta = models.CharField(max_length=50, default='PENDIENTE', null=True, blank=True)
    numero_mfg = models.CharField(max_length=100, default='PENDIENTE', null=True, blank=True)
    # NUEVO CAMPO FOTO
    foto_refaccion = models.BinaryField(null=True, blank=True)
    # NUEVO CAMPO REQUERIMIENTO 1
    cotizado = models.CharField(max_length=50, default='PENDIENTE', null=True, blank=True) 
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, db_column='usuario_id')

    class Meta:
        db_table = 'refacciones'

class Notificacion(models.Model):
    id = models.AutoField(primary_key=True)
    mensaje = models.CharField(max_length=255)
    fecha = models.DateTimeField(default=timezone.now)
    leido = models.BooleanField(default=False)
    url_destino = models.CharField(max_length=100, null=True, blank=True)
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, db_column='usuario_id')

    class Meta:
        db_table = 'notificaciones'