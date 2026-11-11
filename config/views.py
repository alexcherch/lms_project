from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .schema import UNAUTHORIZED, VALIDATION_ERROR


class DocumentedTokenObtainPairView(TokenObtainPairView):
    @extend_schema(
        responses={
            200: TokenObtainPairSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DocumentedTokenRefreshView(TokenRefreshView):
    @extend_schema(
        responses={
            200: TokenRefreshSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
