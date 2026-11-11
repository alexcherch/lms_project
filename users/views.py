from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import generics, serializers, status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.schema import FORBIDDEN, NOT_FOUND, UNAUTHORIZED, VALIDATION_ERROR
from lms.permissions import IsOwner

from .filters import PaymentFilter
from .models import Payment, User
from .serializers import (
    PaymentCreateSerializer,
    PaymentSerializer,
    PublicUserSerializer,
    UserSerializer,
)
from .services import (
    create_stripe_price,
    create_stripe_product,
    create_stripe_session,
    get_stripe_session_status,
)


@extend_schema_view(
    post=extend_schema(
        responses={
            201: UserSerializer,
            400: VALIDATION_ERROR,
        }
    )
)
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    get=extend_schema(
        responses={
            200: UserSerializer(many=True),
            401: UNAUTHORIZED,
        }
    )
)
class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@extend_schema_view(
    get=extend_schema(
        responses={
            200: UserSerializer,
            401: UNAUTHORIZED,
            404: NOT_FOUND,
        }
    ),
    put=extend_schema(
        responses={
            200: UserSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            404: NOT_FOUND,
        }
    ),
    patch=extend_schema(
        responses={
            200: UserSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            404: NOT_FOUND,
        }
    ),
    delete=extend_schema(
        responses={
            204: None,
            401: UNAUTHORIZED,
            404: NOT_FOUND,
        }
    ),
)
class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@extend_schema_view(
    get=extend_schema(
        responses={
            200: UserSerializer,
            401: UNAUTHORIZED,
            404: NOT_FOUND,
        }
    ),
    put=extend_schema(
        responses={
            200: UserSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        }
    ),
    patch=extend_schema(
        responses={
            200: UserSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        }
    ),
)
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


@extend_schema_view(
    get=extend_schema(
        responses={
            200: PaymentSerializer(many=True),
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
        }
    )
)
class PaymentListView(generics.ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ["payment_date"]
    ordering = ["-payment_date"]


class PaymentCreateAPIView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создание платежа",
        description="Создает платеж, обращается к Stripe и возвращает ссылку на оплату.",
        request=PaymentCreateSerializer,
        responses={
            201: PaymentSerializer,
            400: inline_serializer(
                name="PaymentCreateError", fields={"detail": serializers.CharField()}
            ),
            401: UNAUTHORIZED,
        },
    )
    def post(self, request, *args, **kwargs):
        # drf-spectacular ищет аннотацию на HTTP-методе, а не на create()
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        payment = serializer.instance
        return Response(
            PaymentSerializer(payment, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        # 1. Сохраняем платеж, привязывая к текущему пользователю
        payment = serializer.save(user=self.request.user)

        try:
            # 2. Создаем продукт в Stripe
            product = create_stripe_product(
                name=(
                    f"Курс: {payment.course.title}"
                    if payment.course
                    else f"Урок: {payment.lesson.title}"
                ),
                description="Оплата обучения",
            )
            payment.stripe_product_id = product.id

            # 3. Создаем цену в Stripe
            price = create_stripe_price(product.id, payment.amount)
            payment.stripe_price_id = price.id

            # 4. Создаем сессию оплаты
            session = create_stripe_session(
                price_id=price.id,
                success_url="http://127.0.0.1:8000/api/docs/",
                cancel_url="http://127.0.0.1:8000/api/docs/",
            )

            # 5. Сохраняем ссылку и ID сессии
            payment.payment_link = session.url
            payment.session_id = session.id
            payment.save()

        except Exception as e:
            payment.delete()
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {"detail": f"Ошибка при создании платежа в Stripe: {str(e)}"}
            )


class PaymentStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Проверка статуса платежа",
        description="Обращается к Stripe для получения актуального статуса платежа и синхронизирует его с базой.",
        responses={
            200: inline_serializer(
                name="PaymentStatusResponse",
                fields={
                    "payment_id": serializers.IntegerField(),
                    "status": serializers.CharField(),
                    "amount_total": serializers.IntegerField(),
                    "currency": serializers.CharField(),
                },
            ),
            400: inline_serializer(
                name="PaymentStatusError", fields={"error": serializers.CharField()}
            ),
            404: inline_serializer(
                name="PaymentNotFoundError", fields={"detail": serializers.CharField()}
            ),
            401: UNAUTHORIZED,
        },
    )
    def get(self, request, *args, **kwargs):
        payment_id = kwargs.get("pk")
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)

        if not payment.session_id:
            return Response(
                {"error": "У этого платежа нет сессии Stripe"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            session = get_stripe_session_status(payment.session_id)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Синхронизируем статус с нашей моделью
        payment.status = session.payment_status
        payment.save(update_fields=["status"])  # <-- сохраняем только поле status

        return Response(
            {
                "payment_id": payment.id,
                "status": payment.status,  # <-- возвращаем уже сохраненный статус
                "amount_total": session.amount_total,
                "currency": session.currency,
            }
        )
