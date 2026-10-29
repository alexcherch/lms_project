from django.urls import path
from .views import UserUpdateView, PaymentListView

urlpatterns = [
    path('profile/<int:pk>/', UserUpdateView.as_view(), name='user-profile'),
    path('payments/', PaymentListView.as_view(), name='payment-list'),
]
