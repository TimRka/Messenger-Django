from django.urls import path
from django.contrib.auth import views as auth_views
from .views import SignUpView
from .forms import CustomAuthenticationForm

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        authentication_form=CustomAuthenticationForm,
        template_name='registration/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
]
