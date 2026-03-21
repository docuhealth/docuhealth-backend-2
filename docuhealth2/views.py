from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination

from accounts.models import User

class PublicGenericAPIView(generics.GenericAPIView):
    authentication_classes = []  
    permission_classes = [AllowAny]
    
class PublicAPIView():
    authentication_classes = []  
    permission_classes = [AllowAny]
    
class PaginatedView():
    pagination_class = PageNumberPagination
    pagination_class.page_size_query_param = 'size'
    pagination_class.max_page_size = 100
    
class BaseUserCreateView(generics.CreateAPIView):
    
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            if not user.is_verified:
                user.delete()
                
            else:
                return Response({"email": "User with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)
                
        return super().post(request, *args, **kwargs)
