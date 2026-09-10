from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models

class UserManager(DjangoUserManager): 
    """Cuida al modelo si alguien intenta editar su rol mediante create_user() esto
    revienta en vez de aceptarlo.
    Vamos a modificar el método de django para meterle una validación y así evitar que un atacante
    escale privilegios desde el frontend mediante las vistas que utilizan create_user()"""

    def create_user(self, username, email=None, password=None, **extra_fields):
        if 'rol' in extra_fields:
            raise ValueError("No se acepta el parametro 'rol'.")
        extra_fields.setdefault('rol', User.Rol.CLIENTE)
        return super().create_user(username, email, password, **extra_fields)

class User(AbstractUser): #
    class Rol(models.TextChoices): #Subclase de enumeracion, permite hacer cosas como: User.objects.create(rol=User.Rol.MESERO)
        CLIENTE = 'cliente', 'Cliente' #Aquí van todos los roles que queremos, primero el sufijo de base de datos y luego la etiqueta 
        MESERO = 'mesero', 'Mesero' #BD, Etiqueta

    telefono = models.CharField(max_length=20, blank=True)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.CLIENTE)
    objects = UserManager()

    @classmethod
    def crear_mesero(cls, username, email=None, password=None, **extra_fields):
        """Crea explicitamente un mesero. Crea un usuario, define su nuevo rol y luego lo actualiza"""
        usuario = cls.objects.create_user(username, email, password, **extra_fields)
        usuario.rol = cls.Rol.MESERO
        usuario.save(update_fields=['rol'])
        return usuario


    def __str__(self):
        return self.email or self.username
