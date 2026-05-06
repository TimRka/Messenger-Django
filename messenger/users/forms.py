from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import CustomUser


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
        fields = ('username', 'email', 'phone', 'bio', 'avatar', 'birth_date')

class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа"""

    class Meta:
        model = CustomUser