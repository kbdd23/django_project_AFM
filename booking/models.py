from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

class Mesa(models.Model):
    numero = models.PositiveSmallIntegerField(unique=True) #pk
    capacidad = models.PositiveSmallIntegerField() #4, 8, 10, 12
    ubicacion = models.CharField(max_length=50) #terraza, barra, ventana, etc
    es_grande = models.BooleanField(default=False)
    activa = models.BooleanField(default=True) #Softdelete, una mesa NUNCA se borra, solo se desactiva. así nunca pierdes los datos de sus reservas.

    def __str__(self):
        return f"Mesa :{self.numero}"

    @classmethod
    def crear_mesa(cls, numero, capacidad, ubicacion, es_grande=False):
        """Alta controlada de una mesa en el salon."""
        return cls.objects.create(
            numero=numero,
            capacidad=capacidad,
            ubicacion=ubicacion,
            es_grande=es_grande,
        )

    def retirar(self):
        """Soft delete: la mesa sale del salon pero su historia vive."""
        self.activa = False
        self.save(update_fields=['activa'])

    def reactivar(self):
        """Devuelve la mesa al salon."""
        self.activa = True
        self.save(update_fields=['activa'])

    def editar_ubicacion(self, nueva_ubicacion):
        """Edición de la 'ubicación' de una mesa, esto sirve para poder 'orientar' donde está cada mesa
        ejemplo: primer piso-ventana, o ventanal, o editar las mismas mesas inicializadas. (Se crean 8 mesas por defecto al iniciar el proyecto)"""
        self.ubicacion = nueva_ubicacion
        self.save(update_fields=['ubicacion'])

class Reserva(models.Model):
    ESTADO_CONFIRMADO = 'confirmado'
    ESTADO_CANCELADO = 'cancelado'

    ESTADOS = [
        (ESTADO_CONFIRMADO, 'Confirmado'),
        (ESTADO_CANCELADO, 'Cancelado'),
    ]

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas')
    mesa = models.ForeignKey(Mesa, on_delete=models.PROTECT, related_name='reservas')
    fecha = models.DateField()
    hora_inicio = models.TimeField()  # Bloque desde las 14:00
    hora_fin = models.TimeField()     # Bloque hasta las 15:00
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_CONFIRMADO)
    creada_en = models.DateTimeField(auto_now_add=True)  # Trigger -> now()

    def __str__(self):
        return f"Reserva de: {self.cliente} | Mesa: {self.mesa.numero} | Fecha: {self.fecha} | {self.hora_inicio}--{self.hora_fin}"

    class Meta:
        ordering = ['fecha', 'hora_inicio']

    def clean(self):  # clean() es un metodo de django
        super().clean()
        if self.hora_inicio and self.hora_fin and self.hora_fin <= self.hora_inicio:
            raise ValidationError({'hora_fin': 'La hora de fin debe ser posterior a la de inicio'})

    @classmethod  # metodo para calcular el solapamiento de un bloque, evitar choques
    def solapamiento(cls, mesa, fecha, hora_inicio, hora_fin):
        """Devuelve las reservas confirmadas que chocan con ese bloque."""
        return cls.objects.filter(
            mesa=mesa,
            fecha=fecha,
            estado=cls.ESTADO_CONFIRMADO,
            hora_inicio__lt=hora_fin,  # alguna reserva empieza antes de que yo termine
            hora_fin__gt=hora_inicio,  # alguna reserva termina despues de que yo empiece
        )