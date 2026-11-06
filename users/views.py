from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated

from lms.permissions import IsOwner

from .filters import PaymentFilter
from .models import Payment, User
from .serializers import PaymentSerializer, PublicUserSerializer, UserSerializer


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if (
            self.request.method == "GET"
            and self.kwargs.get("pk") != self.request.user.pk
        ):
            return PublicUserSerializer
        return UserSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated, IsOwner]
        return [permission() for permission in self.permission_classes]


class PaymentListView(generics.ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ["payment_date"]
    ordering = ["-payment_date"]
