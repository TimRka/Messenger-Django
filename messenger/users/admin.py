from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Кастомная админка для пользователя"""
    list_display = ['username', 'email', 'phone', 'is_staff']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'phone']

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'bio', 'avatar', 'birth_date')
        }),
        ('Настройки видимости', {
            'fields': ('show_email', 'show_phone', 'show_birth_date', 'show_bio'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('email', 'phone')
        }),
    )
