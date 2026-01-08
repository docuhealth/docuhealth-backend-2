from rest_framework import generics
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
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        
        existing_inactive_user = User.objects.filter(email=email, is_active=False).first()
        if existing_inactive_user:
            print("Deleting existing inactive user")
            existing_inactive_user.delete()  

        return super().post(request, *args, **kwargs)