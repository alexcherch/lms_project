from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from config.celery import app
from lms.models import Course, Lesson, Subscription
from lms.tasks import send_course_update_email
from users.models import User

LOCMEM_MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
}


class CeleryConfigTestCase(APITestCase):
    def test_timezone_matches_django(self):
        self.assertEqual(settings.CELERY_TIMEZONE, settings.TIME_ZONE)
        self.assertEqual(app.conf.timezone, settings.TIME_ZONE)

    def test_deactivate_users_task_is_scheduled(self):
        schedule = settings.CELERY_BEAT_SCHEDULE
        self.assertIn("deactivate-inactive-users", schedule)
        self.assertIn("deactivate-inactive-users", app.conf.beat_schedule)
        self.assertEqual(
            schedule["deactivate-inactive-users"]["task"],
            "users.tasks.deactivate_inactive_users",
        )


@override_settings(MAILERS=LOCMEM_MAILERS)
class CourseUpdateEmailTestCase(APITestCase):
    def setUp(self):
        mail.outbox = []
        self.owner = User.objects.create(email="owner@test.com", password="pass")
        self.subscriber = User.objects.create(
            email="subscriber@test.com", password="pass"
        )
        self.not_subscriber = User.objects.create(
            email="other@test.com", password="pass"
        )
        self.course = Course.objects.create(title="Курс", owner=self.owner)
        Subscription.objects.create(user=self.subscriber, course=self.course)

    def test_task_sends_email_to_subscribers(self):
        sent = send_course_update_email(self.course.id)

        self.assertEqual(sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.subscriber.email])
        self.assertIn(self.course.title, mail.outbox[0].subject)

    def test_task_skips_inactive_subscribers(self):
        self.subscriber.is_active = False
        self.subscriber.save(update_fields=["is_active"])

        sent = send_course_update_email(self.course.id)

        self.assertEqual(sent, 0)
        self.assertEqual(len(mail.outbox), 0)

    @patch("lms.views.send_course_update_email.delay")
    def test_course_update_triggers_task(self, delay):
        self.client.force_authenticate(self.owner)

        response = self.client.patch(
            f"/api/courses/{self.course.id}/",
            {"title": "Обновлённый курс"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delay.assert_called_once_with(self.course.id)


@override_settings(MAILERS=LOCMEM_MAILERS)
class LessonUpdateEmailTestCase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create(email="owner@test.com", password="pass")
        self.course = Course.objects.create(title="Курс", owner=self.owner)
        self.lesson = Lesson.objects.create(
            title="Урок",
            course=self.course,
            video_link="https://youtube.com/watch?v=123",
            owner=self.owner,
        )

    @patch("lms.views.send_course_update_email.delay")
    def test_lesson_update_does_not_notify_within_four_hours(self, delay):
        self.client.force_authenticate(self.owner)

        response = self.client.patch(
            f"/api/lessons/{self.lesson.id}/",
            {"title": "Новое название"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delay.assert_not_called()

    @patch("lms.views.send_course_update_email.delay")
    def test_lesson_update_notifies_after_four_hours(self, delay):
        old_time = timezone.now() - timedelta(hours=5)
        Course.objects.filter(pk=self.course.pk).update(updated_at=old_time)
        self.client.force_authenticate(self.owner)

        response = self.client.patch(
            f"/api/lessons/{self.lesson.id}/",
            {"title": "Новое название"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delay.assert_called_once_with(self.course.id)

        self.course.refresh_from_db()
        self.assertGreater(self.course.updated_at, old_time)
