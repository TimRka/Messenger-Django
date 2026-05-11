from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import CustomUser
from django import forms


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации"""

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['email'].help_text = 'Обязательное поле. Введите действующий email.'


class CustomUserChangeForm(UserChangeForm):
    """Форма изменения пользователя"""

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone', 'bio', 'avatar', 'birth_date',
                  'email_privacy', 'phone_privacy')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('password')
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone'].widget.attrs.update({'class': 'form-control', 'placeholder': '+7XXXXXXXXXX'})
        self.fields['bio'].widget.attrs.update({'class': 'form-control', 'rows': 4})
        self.fields['birth_date'].widget.attrs.update({'class': 'form-control', 'type': 'date'})
        self.fields['avatar'].widget.attrs.update({'class': 'form-control'})

        # Настройки для полей приватности
        self.fields['email_privacy'].widget = forms.Select(choices=CustomUser.PRIVACY_CHOICES)
        self.fields['email_privacy'].widget.attrs.update({'class': 'form-select'})
        self.fields['email_privacy'].label = 'Кто может видеть ваш email'

        self.fields['phone_privacy'].widget = forms.Select(choices=CustomUser.PRIVACY_CHOICES)
        self.fields['phone_privacy'].widget.attrs.update({'class': 'form-select'})
        self.fields['phone_privacy'].label = 'Кто может видеть ваш номер телефона'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            import re
            digits = re.sub(r'\D', '', phone)
            if len(digits) == 10:
                phone = f'+7{digits}'
            elif len(digits) == 11 and digits.startswith('7'):
                phone = f'+{digits}'
            elif len(digits) == 11 and digits.startswith('8'):
                phone = f'+7{digits[1:]}'
            else:
                raise forms.ValidationError('Неверный формат телефона. Используйте +7XXXXXXXXXX')
        return phone


class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа"""

    class Meta:
        model = CustomUser