from django.urls import path
from . import  views
from django.contrib.auth.views import LoginView


urlpatterns = [
    path('logout/', views.register_logout, name='logout'),
    path('', views.register_login, name='login'),
    path('home/', views.home, name='home'),
    path('questions/', views.questions, name='questions'),
    path('behavioral/', views.behavioral, name='behavioral'),
    path('change_pas/', views.change_pas, name='change_pas'),
    path('register/', views.register_register, name='register'),
    path('login/', views.register_login, name='login'),
    path('face-id-login/', views.register_login_face_id, name='face_id_login'),
    path('forget/', views.forget, name='forget'),
    path('authenticator/setup/', views.setup_authenticator, name='setup_authenticator'),
    path('authenticator/login/', views.authenticator_login, name='authenticator_login'),
    path('forget_2', views.forget_pass_step_2, name='forget_2'),
    path('forget_3', views.forget_pass_step_3, name='forget_3'),
]
