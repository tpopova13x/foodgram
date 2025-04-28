
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class that supports the 'limit' query parameter.
    """
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100
