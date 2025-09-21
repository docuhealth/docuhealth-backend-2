from django.core.mail import send_mail

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.parsers import MultiPartParser, FormParser

from medicalrecords.serializers import MedicalRecordSerializer
from medicalrecords.models import MedicalRecord
from core.models import OTP, User, UserProfileImage
from docuhealth2.views import PublicGenericAPIView

from .models import Subaccount
from .serializers import CreateSubaccountSerializer, UpgradeSubaccountSerializer, CreatePatientSerializer, UpdatePatientSerializer, PatientProfileImageSerializer

class CreatePatientView(generics.CreateAPIView, PublicGenericAPIView):
    serializer_class = CreatePatientSerializer
    
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
        
class UpdatePatientView(generics.UpdateAPIView):
    # queryset = User.objects.filter(role='patient')
    serializer_class = UpdatePatientSerializer
    # lookup_field = 'hin'
    
    def get_object(self):
        return self.request.user
    
class PatientDashboardView(generics.GenericAPIView):
    serializer_class = MedicalRecordSerializer  

    def get(self, request, *args, **kwargs):
        patient = request.user  

        queryset = MedicalRecord.objects.filter(patient=patient).order_by("-created_at")
        page = self.paginate_queryset(queryset)
        records_serializer = self.get_serializer(page, many=True)
        
        paginated_data = self.get_paginated_response(records_serializer.data).data
        profile = patient.profile

        return Response({
            "patient_info": {
                "firstname": profile.firstname,
                "lastname": profile.lastname,
                "middlename": profile.middlename,
                "hin": patient.hin,
                "email": patient.email,
                "phone_num": profile.phone_num,
                "emergency": profile.emergency
            },
            **paginated_data
        })
        
class ListCreateSubaccountView(generics.ListCreateAPIView):
    serializer_class = CreateSubaccountSerializer
    
    def get_queryset(self):
        return Subaccount.objects.filter(parent=self.request.user).select_related("parent").order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)
    
class ListSubaccountMedicalRecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    
    def get_queryset(self):
        hin = self.kwargs.get("hin")
        
        if not hin:
            raise ValidationError("Subaccount hin should be provided")
        
        if not User.objects.filter(hin=hin).exists():
            raise NotFound("A subaccount with this HIN does not exist.")
        
        return MedicalRecord.objects.filter(patient__hin = hin).select_related("patient", "hospital").prefetch_related("drug_records", "attachments").order_by('-created_at')
    
class UpgradeSubaccountView(generics.CreateAPIView):
    serializer_class = UpgradeSubaccountSerializer
    
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
        
class UploadPatientProfileImageView(generics.CreateAPIView):
    serializer_class = PatientProfileImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        user = self.request.user
        UserProfileImage.objects.filter(user=user).delete()
        serializer.save(user=user)    