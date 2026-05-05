"""Paginación estándar de la API (HU-07); reutilizada en listados paginados (HU-05, HU-06)."""

from rest_framework.pagination import PageNumberPagination


class APIPageNumberPagination(PageNumberPagination):
    """Alineado con el front: `page`, `page_size` (máx. 50)."""

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
