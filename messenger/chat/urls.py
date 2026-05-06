from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='list'),
    path('<int:chat_id>/', views.chat_room, name='room'),
    path('<int:chat_id>/messages/', views.get_messages, name='messages'),
    path('<int:chat_id>/send/', views.send_message, name='send'),
]