from rest_framework import generics
from rest_framework.permissions import AllowAny

class PublicGenericAPIView(generics.GenericAPIView):
    authentication_classes = []  
    permission_classes = [AllowAny]