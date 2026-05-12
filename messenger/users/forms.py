from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import CustomUser
from django import forms
from .models import UserPreferences


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



class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа"""

    class Meta:
        model = CustomUser
        
class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ['theme', 'font_family', 'font_size']
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-select'}),
            'font_family': forms.Select(attrs={'class': 'form-select'}),
            'font_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 14,
                'max': 20
            }),
        }