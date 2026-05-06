from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя
    """

    email = models.EmailField(unique=True, verbose_name='Email')


    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Телефон'
    )


    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Логин'
    )


    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']