from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot, name='chatbot'),
    path('chatbot/streaming', views.chatbot_streaming, name='chatbot-streaming'),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
    path('chatbot/stop', views.stop_chatbot, name='chatbot-stop'),
    path('upload/', views.upload_pdf, name="upload_pdf"),
    path("task-status/<str:task_id>/", views.check_task_status, name="task_status"),
]