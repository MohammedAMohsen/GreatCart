from django.urls import path
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordChangeView
from django.urls import reverse_lazy
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my-orders/', views.my_orders, name='my-orders'),
    path('profile-setting/', views.profile_setting, name='profile-setting'),


    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),

    # class-Based Reset_Password Views & Change_Password (CBVs)
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
