from django.urls import path
from .views import UserUpdateView

urlpatterns = [
    path('profile/<int:pk>/', UserUpdateView.as_view(), name='user-profile'),
]
