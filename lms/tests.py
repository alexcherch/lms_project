from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson, Subscription
from users.models import User


class LessonTestCase(APITestCase):

    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create(email="test_user@test.com", password="testpass")
        self.moderator = User.objects.create(
            email="moderator@test.com", password="testpass"
        )
        self.other_user = User.objects.create(
            email="other@test.com",
            password="testpass",
        )

        # Добавляем модератора в группу (создаем группу, если её нет)
        from django.contrib.auth.models import Group

        moderators_group, _ = Group.objects.get_or_create(name="moderators")
        self.moderator.groups.add(moderators_group)

        # Создаем курс и урок
        self.course = Course.objects.create(title="Тестовый курс", owner=self.user)
        self.lesson = Lesson.objects.create(
            title="Тестовый урок",
            course=self.course,
            video_link="https://youtube.com/watch?v=123",
            owner=self.user,
        )

    def test_lesson_create(self):
        """Тест создания урока"""
        self.client.force_authenticate(user=self.user)
        data = {
            "title": "Новый урок",
            "course": self.course.id,
            "video_link": "https://youtube.com/watch?v=456",
        }
        response = self.client.post("/api/lessons/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)

    def test_lesson_create_rejects_non_youtube_urls(self):
        self.client.force_authenticate(user=self.user)
        bad_urls = [
            "https://rutube.ru/video/123",
            "https://notyoutube.com/watch?v=1",
            "https://youtube.com.evil.com/watch?v=1",
            "https://evil.com/?youtube.com",
            "https://rutube.ru/youtube.com",
            "https://youtu.be/123",
        ]

        for url in bad_urls:
            with self.subTest(url=url):
                response = self.client.post(
                    "/api/lessons/",
                    {
                        "title": "Плохой урок",
                        "course": self.course.id,
                        "video_link": url,
                    },
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )

        self.assertEqual(Lesson.objects.count(), 1)

    def test_lesson_list(self):
        """Тест получения списка уроков"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что в ответе есть наш урок (учитывая пагинацию)
        self.assertEqual(response.data["count"], 1)

    def test_lesson_update(self):
        """Тест обновления урока"""
        self.client.force_authenticate(user=self.user)
        data = {"title": "Обновленный урок"}
        response = self.client.patch(f"/api/lessons/{self.lesson.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "Обновленный урок")

    def test_lesson_delete(self):
        """Тест удаления урока"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/lessons/{self.lesson.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_lesson_delete_by_moderator(self):
        """Тест: модератор не может удалить урок"""
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(f"/api/lessons/{self.lesson.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_create_by_moderator(self):
        """Тест: модератор не может создать урок"""
        self.client.force_authenticate(user=self.moderator)
        data = {
            "title": "Урок от модератора",
            "course": self.course.id,
        }
        response = self.client.post("/api/lessons/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_retrieve(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/lessons/{self.lesson.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.lesson.id)

    def test_lesson_list_anonymous(self):
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lesson_retrieve_anonymous(self):
        response = self.client.get(f"/api/lessons/{self.lesson.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lesson_retrieve_by_other_user_forbidden(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f"/api/lessons/{self.lesson.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_update_by_other_user_forbidden(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            f"/api/lessons/{self.lesson.id}/",
            {"title": "Чужое изменение"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_delete_by_other_user_forbidden(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(f"/api/lessons/{self.lesson.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_lesson_list_by_other_user_is_empty(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_lesson_retrieve_by_moderator(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.get(f"/api/lessons/{self.lesson.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_lesson_update_by_moderator(self):
        self.client.force_authenticate(user=self.moderator)
        response = self.client.patch(
            f"/api/lessons/{self.lesson.id}/",
            {"title": "Правка модератора"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SubscriptionTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email="sub_user@test.com", password="testpass")
        self.course = Course.objects.create(title="Курс для подписки", owner=self.user)

    def test_subscribe(self):
        """Тест создания подписки"""
        self.client.force_authenticate(user=self.user)
        data = {"course_id": self.course.id}
        response = self.client.post("/api/subscribe/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка добавлена")

    def test_unsubscribe(self):
        """Тест удаления подписки"""
        self.client.force_authenticate(user=self.user)
        # Сначала подписываемся
        self.client.post("/api/subscribe/", {"course_id": self.course.id})
        # Потом отписываемся
        response = self.client.post("/api/subscribe/", {"course_id": self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка удалена")

    def test_subscribe_creates_subscription(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/subscribe/",
            {"course_id": self.course.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка добавлена")
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user,
                course=self.course,
            ).exists()
        )

    def test_unsubscribe_deletes_subscription(self):
        Subscription.objects.create(user=self.user, course=self.course)
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/subscribe/",
            {"course_id": self.course.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка удалена")
        self.assertFalse(
            Subscription.objects.filter(
                user=self.user,
                course=self.course,
            ).exists()
        )

    def test_is_subscribed_flag(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"/api/courses/{self.course.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_subscribed"])

        Subscription.objects.create(user=self.user, course=self.course)

        response = self.client.get(f"/api/courses/{self.course.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_subscribed"])

    def test_subscribe_anonymous(self):
        response = self.client.post(
            "/api/subscribe/",
            {"course_id": self.course.id},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscribe_nonexistent_course(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/subscribe/",
            {"course_id": 999999},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
