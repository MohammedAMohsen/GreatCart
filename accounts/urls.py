from django.urls import path
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),

    # Function-Based Reset_Password Views [FBVs]
    path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset-done/', views.password_reset_done, name='password_reset_done'),
    path('password-change/<uidb64>/<token>/', views.password_change, name='password-change'),
]
