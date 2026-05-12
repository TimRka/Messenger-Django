from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Основные пути
    path('', views.chat_list, name='list'),
    path('create/', views.create_chat, name='create'),
    path('create_direct/<int:user_id>/', views.create_direct_chat, name='create_direct'),
    
    # Чат
    path('<int:chat_id>/', views.chat_room, name='room'),
    path('<int:chat_id>/add/', views.add_member, name='add_member'),
    
    # API для сообщений
    path('<int:chat_id>/messages/', views.get_messages, name='get_messages'),
    path('<int:chat_id>/send/', views.send_message, name='send_message'),
]