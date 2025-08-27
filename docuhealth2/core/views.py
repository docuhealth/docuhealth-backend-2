from django.shortcuts import render
from django.contrib.auth import authenticate

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from .models import User, OTP
from .serializers import UserSerializer, ForgotPasswordSerializer, VerifyOTPSerializer, ResetPasswordSerializer

def set_refresh_cookie(response):
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

    response.data = {"data": {"access_token": access}, "detail": "Access granted", "status": "success"}
            
    return response

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
            
class LoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Send email
        
        if response.status_code == status.HTTP_200_OK:
            set_refresh_cookie(response)
            
        return response
    
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response({"detail": "Please login again"}, status=400)

        request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            set_refresh_cookie(response)
            
        return response
    
class ForgotPassword(GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data["email"]

        # user = authenticate(request, **serializer.validated_data)
        # if not user:
        #     return Response({"detail": "Invalid credentials, please check your email and password", "status": "error"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": f"Invalid email"}, status=status.HTTP_404_NOT_FOUND)

        otp = OTP.generate_otp(user)
        print(otp)
        # TODO: send otp_instance.otp to user.email (via email backend)
        
        return Response({"detail": f"OTP sent successfully"}, status=status.HTTP_200_OK)
    
class VerifyOTPAndGetTokenView(GenericAPIView):
    serializer_class = VerifyOTPSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": f"Invalid email"}, status=status.HTTP_404_NOT_FOUND)

        try:
            otp_instance = user.otps
        except OTP.DoesNotExist:
            return Response({"detail": "No OTP found"}, status=status.HTTP_400_BAD_REQUEST)

        valid, message = otp_instance.verify(otp)
        if not valid:
            return Response({"detail": message, "status": "error"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        print(refresh, refresh.access_token)
        access = str(refresh.access_token)

        response = Response({"data": {"access_token": access}, "detail": "Access granted", "status": "success"}, status=status.HTTP_200_OK,)

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="Lax"
        )

        return response

class ResetPasswordView(GenericAPIView):
    serializer_class = ResetPasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data["email"]
        new_password = serializer.validated_data["new_password"]

        user = request.user
        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password reset successfully"}, status=200)