from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 2  # Количество элементов на странице
    page_size_query_param = (
        "page_size"  # Позволяет клиенту менять размер через ?page_size=5
    )
    max_page_size = 10  # Максимально допустимый размер
