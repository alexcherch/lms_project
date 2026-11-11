from django.core.exceptions import ValidationError


def validate_youtube_url(value):
    if not value:
        return value

    # Проверяем, что ссылка ведёт на youtube.com или www.youtube.com
    if "youtube.com" not in value and "youtu.be" not in value:
        raise ValidationError(
            "Ссылка должна вести только на YouTube. Ссылки на сторонние ресурсы запрещены."
        )
    return value
