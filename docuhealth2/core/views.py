from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import UserSerializer, LoginSerializer, GetOTPSerializer, CustomTokenObtainPairSerializer
from .models import User, OTP
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from django.contrib.auth import authenticate

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(request, **serializer.validated_data)
        if not user:
            return Response({"detail": "Invalid credentials, please check your email and password", "status": "error"}, status=status.HTTP_401_UNAUTHORIZED)

        otp = OTP.generate_otp(user)
        # TODO: send otp_instance.otp to user.email (via email backend)
        
        return Response({"detail": f"OTP sent to {user} successfully"}, status=status.HTTP_200_OK)
    
class VerifyOTPAndGetTokenView(APIView):
    serializer_class = GetOTPSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": f"User with email {email} not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            otp_instance = user.otp
        except OTP.DoesNotExist:
            return Response({"detail": "No OTP found"}, status=status.HTTP_400_BAD_REQUEST)

        valid, message = otp_instance.verify(otp)
        if not valid:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

        # If valid → issue JWT
        serializer = CustomTokenObtainPairSerializer(data={
            "email": email,
            "password": request.data.get("password"),  
        })
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            data = response.data
            refresh = data.get("refresh")
            access = data.get("access")

            response.set_cookie(
                key="refresh_token",
                value=refresh,
                httponly=True,    
                secure=True,      
                samesite="Lax"
            )

            response.data = {"access_token": access, "message": "Logged in successfully"}

        return response
    
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response({"detail": "No refresh token found"}, status=400)

        request.data["refresh"] = refresh_token
        return super().post(request, *args, **kwargs)

