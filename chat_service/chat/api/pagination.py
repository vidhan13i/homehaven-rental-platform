"""
Pagination for chat_service REST API.

Mirrors the pattern in listings_service/listings/api/pagination.py.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class ChatPagination(PageNumberPagination):
    """Standard pagination for conversations and messages."""
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })


class MessagePagination(PageNumberPagination):
    """Pagination for messages — smaller page size, cursor-friendly ordering."""
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })
