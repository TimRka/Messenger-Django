from django.urls import path
from django.contrib.auth import views as auth_views
from .views import SignUpView, profile_view, profile_edit_view, user_search
from .forms import CustomAuthenticationForm

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=CustomAuthenticationForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('search/', user_search, name='user_search'),
]