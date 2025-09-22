from django.core.mail import send_mail

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError, NotFound

from medicalrecords.serializers import MedicalRecordSerializer
from medicalrecords.models import MedicalRecord
from core.models import OTP, User
from docuhealth2.views import PublicGenericAPIView

from .models import SubaccountProfile
from .serializers import CreateSubaccountSerializer, UpgradeSubaccountSerializer, CreatePatientSerializer, UpdatePatientSerializer

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
    serializer_class = UpdatePatientSerializer
    
    def get_object(self):
        return self.request.user
    
class PatientDashboardView(generics.GenericAPIView):
    serializer_class = MedicalRecordSerializer  

    def get(self, request, *args, **kwargs):
        user = request.user
        profile = user.patient_profile 
        print(user) 

        queryset = MedicalRecord.objects.filter(patient=profile).select_related("patient", "subaccount", "hospital").prefetch_related("drug_records", "attachments").order_by("-created_at")
        page = self.paginate_queryset(queryset)
        records_serializer = self.get_serializer(page, many=True)
        
        paginated_data = self.get_paginated_response(records_serializer.data).data

        return Response({
            "patient_info": {
                "firstname": profile.firstname,
                "lastname": profile.lastname,
                "middlename": profile.middlename,
                "hin": profile.hin,
                "email": user.email,
                "phone_num": profile.phone_num,
                "emergency": profile.emergency
            },
            **paginated_data
        })
        
class ListCreateSubaccountView(generics.ListCreateAPIView):
    serializer_class = CreateSubaccountSerializer
    
    def get_queryset(self):
        return SubaccountProfile.objects.filter(parent=self.request.user.patient_profile).select_related("parent").order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(parent=self.request.user.patient_profile)
    
class ListSubaccountMedicalRecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    
    def get_queryset(self):
        hin = self.kwargs.get("hin")
        
        if not hin:
            raise ValidationError("Subaccount hin should be provided")
        
        if not SubaccountProfile.objects.filter(hin=hin).exists():
            raise NotFound("A subaccount with this HIN does not exist.")
        
        return MedicalRecord.objects.filter(subaccount__hin = hin).select_related("patient", "subaccount", "hospital").prefetch_related("drug_records", "attachments").order_by('-created_at')
    
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
        