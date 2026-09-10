from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model. Se crea desde el día 1 aunque hoy solo agregue
    'email' como identificador único — cambiar esto después de la
    primera migración obliga a reconstruir la base de datos.
    """

    email = models.EmailField(unique=True)
    currency_preference = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username