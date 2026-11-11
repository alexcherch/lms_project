from drf_spectacular.utils import OpenApiResponse

UNAUTHORIZED = OpenApiResponse(description="Требуется авторизация")
FORBIDDEN = OpenApiResponse(description="Недостаточно прав")
NOT_FOUND = OpenApiResponse(description="Объект не найден")
VALIDATION_ERROR = OpenApiResponse(description="Ошибка валидации данных")
