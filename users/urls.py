from django.urls import path

from .views import (
    PaymentListView,
    UserCreateView,
    UserListAPIView,
    UserRetrieveUpdateDestroyAPIView,
    UserUpdateView,
)

urlpatterns = [
    path("register/", UserCreateView.as_view(), name="user-register"),
    path("", UserListAPIView.as_view(), name="user-list"),
    path("<int:pk>/", UserRetrieveUpdateDestroyAPIView.as_view(), name="user-detail"),
    path("profile/<int:pk>/", UserUpdateView.as_view(), name="user-profile"),
    path("payments/", PaymentListView.as_view(), name="payment-list"),
]
