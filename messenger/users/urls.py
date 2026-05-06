from django.urls import path
from django.contrib.auth import views as auth_views
from .views import SignUpView
from .forms import CustomAuthenticationForm
from django.views.generic import TemplateView

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
]
