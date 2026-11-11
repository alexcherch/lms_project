from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Course, Lesson, Subscription
from .validators import validate_youtube_url


class LessonSerializer(serializers.ModelSerializer):
    video_link = serializers.URLField(
        validators=[validate_youtube_url],
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    class Meta:
        model = Lesson
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()

    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = "__all__"

    @extend_schema_field(serializers.IntegerField())
    def get_lessons_count(self, obj):
        return obj.lessons.count()

    @extend_schema_field(serializers.BooleanField())
    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, course=obj).exists()
        return False


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = "__all__"
