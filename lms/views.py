from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import generics, serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.schema import FORBIDDEN, NOT_FOUND, UNAUTHORIZED, VALIDATION_ERROR

from .models import Course, Lesson, Subscription
from .paginators import CustomPagination
from .permissions import IsModer, IsOwner
from .serializers import CourseSerializer, LessonSerializer


@extend_schema_view(
    list=extend_schema(
        responses={
            200: CourseSerializer(many=True),
            401: UNAUTHORIZED,
        }
    ),
    create=extend_schema(
        responses={
            201: CourseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        }
    ),
    retrieve=extend_schema(
        responses={
            200: CourseSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        }
    ),
    update=extend_schema(
        responses={
            200: CourseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        }
    ),
    partial_update=extend_schema(
        responses={
            200: CourseSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        }
    ),
    destroy=extend_schema(
        responses={
            204: None,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        }
    ),
)
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [IsAuthenticated, ~IsModer]
        elif self.action in ["update", "partial_update", "retrieve"]:
            self.permission_classes = [IsAuthenticated, IsModer | IsOwner]
        elif self.action == "destroy":
            self.permission_classes = [IsAuthenticated, IsOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="moderators").exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)


@extend_schema_view(
    get=extend_schema(
        responses={
            200: LessonSerializer(many=True),
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        }
    ),
    post=extend_schema(
        responses={
            201: LessonSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
        }
    ),
)
class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, ~IsModer]
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="moderators").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


@extend_schema_view(
    get=extend_schema(
        responses={
            200: LessonSerializer,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        }
    ),
    put=extend_schema(
        responses={
            200: LessonSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        }
    ),
    patch=extend_schema(
        responses={
            200: LessonSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        }
    ),
    delete=extend_schema(
        responses={
            204: None,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            404: NOT_FOUND,
        }
    ),
)
class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "PUT", "PATCH"]:
            self.permission_classes = [IsAuthenticated, IsModer | IsOwner]
        elif self.request.method == "DELETE":
            self.permission_classes = [IsAuthenticated, IsOwner]
        return [permission() for permission in self.permission_classes]


class SubscriptionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Управление подпиской на курс",
        description="Если подписка есть — удаляет её. Если нет — создаёт.",
        request=inline_serializer(
            name="SubscriptionRequest", fields={"course_id": serializers.IntegerField()}
        ),
        responses={
            200: inline_serializer(
                name="SubscriptionResponse", fields={"message": serializers.CharField()}
            ),
            401: UNAUTHORIZED,
            404: OpenApiResponse(description="Курс не найден"),
        },
    )
    def post(self, *args, **kwargs):
        user = self.request.user
        course_id = self.request.data.get("course_id")

        course_item = get_object_or_404(Course, id=course_id)

        subs_item = Subscription.objects.filter(user=user, course=course_item)

        if subs_item.exists():
            subs_item.delete()
            message = "Подписка удалена"
        else:
            Subscription.objects.create(user=user, course=course_item)
            message = "Подписка добавлена"

        return Response({"message": message}, status=status.HTTP_200_OK)
