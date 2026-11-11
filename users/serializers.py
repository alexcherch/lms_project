from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Payment, User


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = (
            "user",
            "stripe_product_id",
            "stripe_price_id",
            "payment_link",
            "session_id",
            "status",
        )


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("amount", "payment_method", "course", "lesson")

    def validate(self, data):
        course = data.get("course")
        lesson = data.get("lesson")

        if course and lesson:
            raise serializers.ValidationError(
                "Нельзя оплачивать одновременно и курс, и урок. Выберите что-то одно."
            )
        if not course and not lesson:
            raise serializers.ValidationError(
                "Необходимо указать либо курс, либо урок для оплаты."
            )
        return data


class UserSerializer(serializers.ModelSerializer):
    payments = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "phone", "city", "avatar", "payments"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    @extend_schema_field(PaymentSerializer(many=True))
    def get_payments(self, obj):
        user_payments = Payment.objects.filter(user=obj)
        return PaymentSerializer(user_payments, many=True).data


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "phone", "city", "avatar"]
