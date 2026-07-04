from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """Default pagination: 20 items per page, customizable via ?page_size=N."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "results": data,
            }
        )


class LargeResultsSetPagination(PageNumberPagination):
    """For endpoints that return large datasets (50 per page)."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class CustomLimitOffsetPagination(LimitOffsetPagination):
    """Offset-based pagination: ?limit=20&offset=40."""

    default_limit = 20
    max_limit = 100
