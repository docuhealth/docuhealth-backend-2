from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import extend_schema

from .models import User, OTP, UserProfileImage
from .serializers import ForgotPasswordSerializer, VerifyOTPSerializer, ResetPasswordSerializer, UserProfileImageSerializer, UpdatePasswordSerializer
from .requests import verify_nin_request

from patients.models import NINVerificationAttempt, PatientProfile
from patients.serializers import VerifyUserNINSerializer
from patients.utils import *

from docuhealth2.views import PublicGenericAPIView
from docuhealth2.permissions import IsAuthenticatedHospitalStaff, IsAuthenticatedPatient
from docuhealth2.utils.email_service import BrevoEmailService
from patients.serializers import PatientBasicInfoSerializer

mailer = BrevoEmailService()

def set_refresh_cookie(response):
    data = response.data
    
    refresh = data.get("refresh")
    access = data.get("access")
    
    print("Access Token:", access)

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,    
        secure=True,      
        samesite="None"
    )

    response.data = {"data": {"access_token": access}, "detail": "Access granted", "status": "success"}
            
    return response

@extend_schema(tags=["Auth"])
class ListUserView(generics.ListAPIView):
    queryset = User.objects.exclude(role="subaccount").order_by("-created_at")
    serializer_class = PatientBasicInfoSerializer
      
@extend_schema(tags=["Auth"])  
class VerifySignupOTPView(PublicGenericAPIView):  
    serializer_class = VerifyOTPSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        valid, message = serializer.otp_instance.verify(serializer.otp)
        if not valid:
            return Response({"detail": message, "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.user.is_active = True
        serializer.user.save(update_fields=['is_active'])
        
        response = {"detail": f"Email verified successfully, proceed to login"}
        
        if serializer.user.role == User.Role.PATIENT:
            response["hin"] = serializer.user.patient_profile.hin
            
        return Response(response, status=status.HTTP_200_OK)

@extend_schema(tags=["Auth"])  
class LoginView(TokenObtainPairView, PublicGenericAPIView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        email = request.data.get("email")
        
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.get(email=email)
            role = user.role
            
            if role == User.Role.PATIENT:
                profile = user.patient_profile
                if not profile.nin_verified:
                    return Response({"detail": "NIN not verified. Kindly verify your NIN", "status": "error", "hin": profile.hin}, status=status.HTTP_403_FORBIDDEN)
            
            set_refresh_cookie(response)
            
            response.data["data"]["role"] = role
            
            if role == User.Role.HOSPITAL_STAFF:
                staff_profile = user.hospital_staff_profile
                hospital = staff_profile.hospital
                staff_role = staff_profile.role
                
                hospital_data = {
                    "name": hospital.name,
                    "hin": hospital.hin
                }
                
                response.data["data"]["hospital"] = hospital_data
                response.data["data"]["staff_role"] = staff_role
                
            mailer.send(
                subject="New Login Alert",
                body = "There was a login attempt on your DOCUHEALTH account. If this was you, you can ignore this message. \n\nIf this was not you, please contact our support team at support@docuhealthservices.com \n\n\nFrom the Docuhealth Team",
                recipient=email,         
            )
                
        return response

@extend_schema(tags=["Auth"])  
class ForgotPassword(PublicGenericAPIView):
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        otp = OTP.generate_otp(serializer.user)
        print(otp)
        
        mailer.send(
            subject="Account Recovery",
            body = (
                        f"Enter the OTP below into the required field \n"
                        f"The OTP will expire in 10 mins\n\n"
                        f"OTP: {otp} \n\n"
                        f"If you did not iniate this request, please contact our support team at support@docuhealthservices.com   \n\n\n"
                        f"From the Docuhealth Team"
                    ),
            recipient=serializer.email,    
        )
        
        return Response({"detail": f"OTP sent successfully"}, status=status.HTTP_200_OK)

@extend_schema(tags=["Auth"])  
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

@extend_schema(tags=["Auth"])  
class ResetPasswordView(GenericAPIView):
    serializer_class = ResetPasswordSerializer
    
    def patch(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_password = serializer.validated_data["new_password"]

        user = request.user
        user.set_password(new_password)
        user.save(update_fields=['password'])

        return Response({"detail": "Password reset successfully. Please log in with your new credentials.", "status": "success"}, status=200)

@extend_schema(tags=["Auth"])  
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        
        if not refresh_token:
            return Response({"detail": "Please login again"}, status=400)
        
        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        
        set_refresh_cookie(response)
        
        return response

@extend_schema(tags=["api"])  
class UploadUserProfileImageView(generics.CreateAPIView):
    serializer_class = UserProfileImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        user = self.request.user
        UserProfileImage.objects.filter(user=user).delete()
        serializer.save(user=user) 
        
@extend_schema(tags=['Auth'], summary="Update hospital staff account password")
class UpdatePasswordView(generics.GenericAPIView):
    serializer_class = UpdatePasswordSerializer
    permission_classes = [IsAuthenticatedHospitalStaff]
    
    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password reset successfully. Please log in with your new credentials.", "status": "success"}, status=200)
   
@extend_schema(tags=["Auth"])   
class VerifyUserNINView(PublicGenericAPIView, generics.GenericAPIView):
    serializer_class = VerifyUserNINSerializer
    
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        nin = serializer.validated_data["nin"]
        patient_profile = serializer.validated_data["patient"]
        patient_profile = (PatientProfile.objects.select_for_update().get(id=patient_profile.id))
        
        user = patient_profile.user
        
        if patient_profile.nin_verified:
            return self._generate_login_response(user)
        
        nin_hash = hash_nin(nin)
        
        if PatientProfile.objects.filter(nin_hash=nin_hash).exists():
            return Response({"detail": "This NIN is already associated with another account."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not can_attempt_nin_verification(user):
            return Response({"detail": "You have reached the maximum number of attempts to verify your NIN today. Please contact our support team for assistance."}, status=status.HTTP_400_BAD_REQUEST)
        
        if nin_checked_before(user, nin_hash):
            return Response({"detail": "This NIN has already been checked and is invalid."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reference = verify_nin_request(nin)
        except Exception as e:
            NINVerificationAttempt.objects.create(user=user, nin_hash=nin_hash, success=False)
            return Response({"detail": str(e)}, status=400)
        
        NINVerificationAttempt.objects.create(user=user, nin_hash=nin_hash, success=True)

        patient_profile.nin_verified = True
        patient_profile.nin_hash = nin_hash
        patient_profile.save(update_fields=['nin_verified', 'nin_hash'])
        
        return self._generate_login_response(user)
    
    def _generate_login_response(self, user):
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        data = {
                "access": access,
                "refresh": str(refresh),
            }

        response = Response(data, status=200)

        set_refresh_cookie(response)
        response.data["data"]["role"] = user.role
        
        mailer.send(
                subject="New Login Alert",
                body = "There was a login attempt on your DOCUHEALTH account. If this was you, you can ignore this message. \n\nIf this was not you, please contact our support team at support@docuhealthservices.com \n\n\nFrom the Docuhealth Team",
                recipient=user.email,         
            )

        return response