from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandartPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = 'page_size'
    max_page_size = 2000


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'limit'
    page_query_param = 'offset'
    max_page_size = 10000


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'limit'
    page_query_param = 'page'
    max_page_size = 100000
    
    def get_paginated_response(self, data):
        return Response({
            'count':len(data),
            'total_pages': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class MediumResultsSetPagination(PageNumberPagination):
    page_size = 22
    page_size_query_param = 'limit'
    page_query_param = 'offset'
    max_page_size = 200