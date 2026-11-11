from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from lms.models import Course, Lesson
from users.models import User


class LessonTestCase(APITestCase):

    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create(email='test_user@test.com', password='testpass')
        self.moderator = User.objects.create(email='moderator@test.com', password='testpass')

        # Добавляем модератора в группу (создаем группу, если её нет)
        from django.contrib.auth.models import Group
        moderators_group, _ = Group.objects.get_or_create(name='moderators')
        self.moderator.groups.add(moderators_group)

        # Создаем курс и урок
        self.course = Course.objects.create(title='Тестовый курс', owner=self.user)
        self.lesson = Lesson.objects.create(
            title='Тестовый урок',
            course=self.course,
            video_link='https://youtube.com/watch?v=123',
            owner=self.user
        )

    def test_lesson_create(self):
        """Тест создания урока"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Новый урок',
            'course': self.course.id,
            'video_link': 'https://youtube.com/watch?v=456'
        }
        response = self.client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)

    def test_lesson_create_invalid_url(self):
        """Тест создания урока с неверной ссылкой"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Урок с плохой ссылкой',
            'course': self.course.id,
            'video_link': 'https://rutube.ru/video/123'
        }
        response = self.client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lesson_list(self):
        """Тест получения списка уроков"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Проверяем, что в ответе есть наш урок (учитывая пагинацию)
        self.assertEqual(response.data['count'], 1)

    def test_lesson_update(self):
        """Тест обновления урока"""
        self.client.force_authenticate(user=self.user)
        data = {'title': 'Обновленный урок'}
        response = self.client.patch(f'/api/lessons/{self.lesson.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, 'Обновленный урок')

    def test_lesson_delete(self):
        """Тест удаления урока"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_lesson_delete_by_moderator(self):
        """Тест: модератор не может удалить урок"""
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(f'/api/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_create_by_moderator(self):
        """Тест: модератор не может создать урок"""
        self.client.force_authenticate(user=self.moderator)
        data = {
            'title': 'Урок от модератора',
            'course': self.course.id,
        }
        response = self.client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubscriptionTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email='sub_user@test.com', password='testpass')
        self.course = Course.objects.create(title='Курс для подписки', owner=self.user)

    def test_subscribe(self):
        """Тест создания подписки"""
        self.client.force_authenticate(user=self.user)
        data = {'course_id': self.course.id}
        response = self.client.post('/api/subscribe/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Подписка добавлена')

    def test_unsubscribe(self):
        """Тест удаления подписки"""
        self.client.force_authenticate(user=self.user)
        # Сначала подписываемся
        self.client.post('/api/subscribe/', {'course_id': self.course.id})
        # Потом отписываемся
        response = self.client.post('/api/subscribe/', {'course_id': self.course.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Подписка удалена')
