from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from users.models import User
from users.tasks import deactivate_inactive_users


class DeactivateInactiveUsersTestCase(APITestCase):
    def test_deactivates_only_users_inactive_for_more_than_month(self):
        old_user = User.objects.create(email="old@test.com", password="pass")
        recent_user = User.objects.create(email="recent@test.com", password="pass")
        never_logged_in = User.objects.create(email="never@test.com", password="pass")
        superuser = User.objects.create_superuser(
            email="admin@test.com", password="pass"
        )

        old_login = timezone.now() - timedelta(days=40)
        User.objects.filter(pk=old_user.pk).update(last_login=old_login)
        User.objects.filter(pk=recent_user.pk).update(
            last_login=timezone.now() - timedelta(days=10)
        )
        User.objects.filter(pk=superuser.pk).update(last_login=old_login)

        updated = deactivate_inactive_users()

        self.assertEqual(updated, 1)
        old_user.refresh_from_db()
        recent_user.refresh_from_db()
        never_logged_in.refresh_from_db()
        superuser.refresh_from_db()
        self.assertFalse(old_user.is_active)
        self.assertTrue(recent_user.is_active)
        self.assertTrue(never_logged_in.is_active)
        self.assertTrue(superuser.is_active)
