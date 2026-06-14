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

    # class-Based Reset_Password Views [CBVs]
    path('password-reset/',
        PasswordResetView.as_view(template_name='accounts/password_reset.html'),
        name='password_reset'
    ),
    path('password-reset-done/',
        PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='password_reset_done'
    ),
    path('reset/<uidb64>/<token>/',
        views.CustomPasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
]
