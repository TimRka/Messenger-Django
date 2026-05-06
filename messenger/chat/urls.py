from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='list'),
    path('create/', views.create_chat, name='create'),
    path('<int:chat_id>/', views.chat_room, name='room'),
    path('<int:chat_id>/add/', views.add_member, name='add_member'),
    path('<int:chat_id>/messages/', views.get_messages, name='messages'),
    path('<int:chat_id>/send/', views.send_message, name='send'),
]