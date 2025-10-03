from django.core.mail import send_mail

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError, NotFound

from medicalrecords.serializers import MedicalRecordSerializer, ListMedicalRecordsSerializer
from medicalrecords.models import MedicalRecord
from core.models import OTP, User
from appointments.models import Appointment

from docuhealth2.views import PublicGenericAPIView
from docuhealth2.permissions import IsAuthenticatedPatient

from drf_spectacular.utils import extend_schema

from .models import SubaccountProfile
from .serializers import CreateSubaccountSerializer, UpgradeSubaccountSerializer, CreatePatientSerializer, UpdatePatientSerializer, PatientAppointmentSerializer

@extend_schema(tags=["Patient"])
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
        
@extend_schema(tags=["Patient"])
class UpdatePatientView(generics.UpdateAPIView):
    serializer_class = UpdatePatientSerializer
    permission_classes = [IsAuthenticatedPatient]
    http_method_names = ['patch']
    
    def get_object(self):
        return self.request.user

@extend_schema(tags=["Patient"])
class PatientDashboardView(generics.GenericAPIView):
    serializer_class = ListMedicalRecordsSerializer
    permission_classes = [IsAuthenticatedPatient]

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
                "dob": profile.dob,
                "id_card_generated": profile.id_card_generated,
                "email": user.email,
                "phone_num": profile.phone_num,
                "emergency": profile.emergency
            },
            **paginated_data
        })
    
@extend_schema(tags=["Patient"])   
class ListCreateSubaccountView(generics.ListCreateAPIView):
    serializer_class = CreateSubaccountSerializer
    permission_classes = [IsAuthenticatedPatient]
    
    def get_queryset(self):
        return SubaccountProfile.objects.filter(parent=self.request.user.patient_profile).select_related("parent").order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(parent=self.request.user.patient_profile)

@extend_schema(tags=["auth"])  
class ListSubaccountMedicalRecordsView(generics.ListAPIView):
    serializer_class = ListMedicalRecordsSerializer
    permission_classes = [IsAuthenticatedPatient]
    
    def get_queryset(self):
        hin = self.kwargs.get("hin")
        
        if not hin:
            raise ValidationError("Subaccount hin should be provided")
        
        if not SubaccountProfile.objects.filter(hin=hin).exists():
            raise NotFound("A subaccount with this HIN does not exist.")
        
        return MedicalRecord.objects.filter(subaccount__hin = hin).select_related("patient", "subaccount", "hospital").prefetch_related("drug_records", "attachments").order_by('-created_at')

@extend_schema(tags=["Patient"])
class UpgradeSubaccountView(generics.CreateAPIView):
    serializer_class = UpgradeSubaccountSerializer
    permission_classes = [IsAuthenticatedPatient]
    
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
    
@extend_schema(tags=["Patient"])
class ListAppointmentsView(generics.ListAPIView):
    serializer_class = PatientAppointmentSerializer
    permission_classes = [IsAuthenticatedPatient]
    
    def get_queryset(self):
        user = self.request.user
        
        return Appointment.objects.filter(patient=user.patient_profile).select_related("doctor", "hospital").order_by('-scheduled_time')

@extend_schema(tags=["Patient"])
class DeletePatientAccountView(generics.DestroyAPIView):
    serializer_class = UpdatePatientSerializer
    permission_classes = [IsAuthenticatedPatient]
    
    def get_object(self):
        return self.request.user
    
    def perform_destroy(self, instance):
        profile = instance.patient_profile
        profile.soft_delete()
        
        