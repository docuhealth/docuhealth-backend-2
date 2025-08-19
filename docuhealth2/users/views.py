from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserSerializer

class UserCreateView(generics.CreateAPIView):
    serializer_class = UserSerializer

    # Optional: customize the response
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # You can return the serialized user
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)