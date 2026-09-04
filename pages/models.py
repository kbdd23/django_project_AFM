from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    telefono = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.email or self.username
