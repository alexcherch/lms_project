from celery import shared_task
from django.conf import settings
from django.core.mail import send_mass_mail

from .models import Course, Subscription


@shared_task
def send_course_update_email(course_id):
    """
    Отправляет письмо об обновлении курса всем его подписчикам.
    """
    course = Course.objects.filter(pk=course_id).first()
    if course is None:
        return 0

    emails = list(
        Subscription.objects.filter(course=course, user__is_active=True)
        .select_related("user")
        .values_list("user__email", flat=True)
    )
    if not emails:
        return 0

    subject = f"Обновление курса «{course.title}»"
    message = (
        f"Материалы курса «{course.title}» были обновлены.\n"
        "Проверьте новые уроки и материалы в личном кабинете."
    )
    messages = [
        (subject, message, settings.DEFAULT_FROM_EMAIL, [email]) for email in emails
    ]

    send_mass_mail(messages, fail_silently=False)
    return len(messages)
