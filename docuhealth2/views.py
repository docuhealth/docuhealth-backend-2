from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination

class PublicGenericAPIView(generics.GenericAPIView):
    authentication_classes = []  
    permission_classes = [AllowAny]
    
class PaginatedView():
    pagination_class = PageNumberPagination
    pagination_class.page_size_query_param = 'size'
    pagination_class.max_page_size = 100