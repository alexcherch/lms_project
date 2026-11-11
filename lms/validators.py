from urllib.parse import urlparse

from django.core.exceptions import ValidationError

ERROR_MESSAGE = (
    "Ссылка должна вести только на YouTube. " "Ссылки на сторонние ресурсы запрещены."
)


def validate_youtube_url(value):
    if not value:
        return value

    try:
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        raise ValidationError(ERROR_MESSAGE)

    # http/https + домен youtube.com или его поддомен
    is_youtube_host = host == "youtube.com" or host.endswith(".youtube.com")

    if parsed.scheme not in {"http", "https"} or not is_youtube_host:
        raise ValidationError(ERROR_MESSAGE)

    return value
