from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя
    """
    #нынче обязателен
    email = models.EmailField(unique=True, verbose_name='Email')
    #необязателен
    phone_regex = RegexValidator(
        regex=r'^\+?7?\d{10}$',
        message="Телефон в формате: +7XXXXXXXXXX (10 цифр)"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Телефон'
    )
    #доп инфа
    birth_date = models.DateField(blank=True, null=True, verbose_name='Дата рождения')
    bio = models.TextField(blank=True, null=True, verbose_name='О себе')
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    last_online = models.DateTimeField(auto_now=True, verbose_name='Был в сети')


    # Поля для параметров входа
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username