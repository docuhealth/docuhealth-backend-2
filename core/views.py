from django.core.mail import send_mail

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.generics import GenericAPIView

from .models import User, OTP
from .serializers import CreateUserSerializer, ForgotPasswordSerializer, VerifyOTPSerializer, ResetPasswordSerializer

from docuhealth2.views import PublicGenericAPIView

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

class CreateUserView(generics.CreateAPIView, PublicGenericAPIView):
    serializer_class = CreateUserSerializer
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        
        existing_inactive_user = User.objects.filter(email=email, is_active=False).first()
        if existing_inactive_user:
            existing_inactive_user.delete()  

        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = serializer.save()
        otp = OTP.generate_otp(user)
        
        send_mail(
            subject="Verify your email",
            message=(
                f"Enter the OTP below into the required field \n"
                f"The OTP will expire in 10 mins\n\n"
                f"OTP: {otp}\n\n"
                f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
                f"From the Docuhealth Team"
            ),
            recipient_list=[user.email],
            from_email=None,
        )
        
class ListUserView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = CreateUserSerializer
        
class VerifyEmailOTPView(PublicGenericAPIView):  
    serializer_class = VerifyOTPSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        valid, message = serializer.otp_instance.verify(serializer.otp)
        if not valid:
            return Response({"detail": message, "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.user.is_active = True
        serializer.user.save(update_fields=['is_active'])
        
        return Response({"detail": f"Email verified successfully, proceed to login"}, status=status.HTTP_200_OK)
    
class LoginView(TokenObtainPairView, PublicGenericAPIView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        send_mail(
            subject="New Login Alert",
            message= "There was a login attempt on your DOCUHEALTH account. If this was you, you can ignore this message. \n\nIf this was not you, please contact our support team at support@docuhealthservices.com \n\n\nFrom the Docuhealth Team",
            from_email=None,
            recipient_list=[request.data.get("email")],         
        )
        
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.get(email=request.data.get("email"))
            role = user.role
            
            set_refresh_cookie(response)
            response.data["data"]["role"] = role
            
        return response
    
    
class ForgotPassword(PublicGenericAPIView):
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        otp = OTP.generate_otp(serializer.user)
        print(otp)
        
        send_mail(
            subject="Account Recovery",
            message= (
                        f"Enter the OTP below into the required field \n"
                        f"The OTP will expire in 10 mins\n\n"
                        f"OTP: {otp} \n\n"
                        f"If you did not iniate this request, please contact our support team at support@docuhealthservices.com   \n\n\n"
                        f"From the Docuhealth Team"
                    ),
            recipient_list=[serializer.email],
            from_email=None,
        )
        
        return Response({"detail": f"OTP sent successfully"}, status=status.HTTP_200_OK)
    
class VerifyForgotPasswordOTPView(PublicGenericAPIView):
    serializer_class = VerifyOTPSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        valid, message = serializer.otp_instance.verify(serializer.otp)
        if not valid:
            return Response({"detail": message, "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        access = AccessToken.for_user(serializer.user)

        response = Response({"data": {"access_token": str(access)}, "detail": "Access granted to reset password", "status": "success"}, status=status.HTTP_200_OK,)

        return response
    
class ResetPasswordView(GenericAPIView):
    serializer_class = ResetPasswordSerializer
    
    def patch(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_password = serializer.validated_data["new_password"]

        user = request.user
        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password reset successfully. Please log in with your new credentials.", "status": "success"}, status=200)
    
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        print(refresh_token)
        if refresh_token is None:
            return Response({"detail": "Please login again"}, status=400)

        request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            set_refresh_cookie(response)
            
        return response