from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User

class UserTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email='user_test@test.com', password='testpass')

    def test_user_registration(self):
        """Тест регистрации нового пользователя"""
        data = {
            'email': 'new_user@test.com',
            'password': 'newpassword123'
        }
        response = self.client.post('/api/users/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

    def test_user_profile_view(self):
        """Тест просмотра профиля (только для авторизованных)"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/users/profile/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user_test@test.com')
