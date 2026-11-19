from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import User

INACTIVE_USER_DAYS = 30


@shared_task
def deactivate_inactive_users():
    """
    Блокирует пользователей, которые не заходили более месяца.
    Обновление выполняется одним запросом, без перебора в Python.
    """
    threshold = timezone.now() - timedelta(days=INACTIVE_USER_DAYS)

    return User.objects.filter(
        is_active=True,
        is_superuser=False,
        last_login__isnull=False,
        last_login__lt=threshold,
    ).update(is_active=False)
