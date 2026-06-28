from django.urls import path
from . import views

urlpatterns = [
    path('place-order/', views.place_order, name='place-order'),
    path('payments/', views.payments, name='payments'),
    path('payments/<str:order_number>/', views.payment_page, name='payment_page'),
    path('order-complete/', views.order_complete, name='order_complete'),
    path('cancel-order/<str:order_number>/', views.cancel_order, name='cancel-order'),
]