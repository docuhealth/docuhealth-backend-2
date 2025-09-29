from django.core.mail import send_mail

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.parsers import MultiPartParser, FormParser

from medicalrecords.serializers import MedicalRecordSerializer
from medicalrecords.models import MedicalRecord
from core.models import OTP, User, UserProfileImage
from docuhealth2.views import PublicGenericAPIView, BaseUserCreateView
from docuhealth2.permissions import IsAuthenticatedHospital

from drf_spectacular.utils import extend_schema

from .models import HospitalProfile, DoctorProfile
from .serializers import CreateHospitalSerializer, CreateDoctorSerializer

@extend_schema(tags=["Hospital"])  
class CreateHospitalView(BaseUserCreateView, PublicGenericAPIView):
    serializer_class = CreateHospitalSerializer
    
    def perform_create(self, serializer):
        user = serializer.save()
        otp = OTP.generate_otp(user)
        
        # send_mail(
        #     subject="Verify your email",
        #     message=(
        #         f"Enter the OTP below into the required field \n"
        #         f"The OTP will expire in 10 mins\n\n"
        #         f"OTP: {otp}\n\n"
        #         f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
        #         f"From the Docuhealth Team"
        #     ),
        #     recipient_list=[user.email],
        #     from_email=None,
        # )
        
@extend_schema(tags=["Hospital"])  
class CreateDoctorView(BaseUserCreateView):
    serializer_class = CreateDoctorSerializer
    permission_classes = [IsAuthenticatedHospital]
    
    def perform_create(self, serializer):
        user = serializer.save()
        otp = OTP.generate_otp(user)
        
        # send_mail(
        #     subject="Verify your email",
        #     message=(
        #         f"Enter the OTP below into the required field \n"
        #         f"The OTP will expire in 10 mins\n\n"
        #         f"OTP: {otp}\n\n"
        #         f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
        #         f"From the Docuhealth Team"
        #     ),
        #     recipient_list=[user.email],
        #     from_email=None,
        # )
        
        