from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """50 items per page by default. Screens that need everything at once (e.g. the floor map's
    70 beds) can ask for more with ?page_size=..., up to a safe maximum."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500
