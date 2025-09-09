from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError

from medicalrecords.serializers import MedicalRecordSerializer
from medicalrecords.models import MedicalRecord
from core.models import OTP

from .models import Subaccount
from .serializers import CreateSubaccountSerializer, UpgradeSubaccountSerializer

class PatientDashboardView(generics.GenericAPIView):
    serializer_class = MedicalRecordSerializer  

    def get(self, request, *args, **kwargs):
        patient = request.user  

        queryset = MedicalRecord.objects.filter(patient=patient).order_by("-created_at")
        page = self.paginate_queryset(queryset)
        records_serializer = self.get_serializer(page, many=True)
        
        paginated_data = self.get_paginated_response(records_serializer.data).data

        return Response({
            "patient_info": {
                "firstname": patient.profile.firstname,
                "lastname": patient.profile.lastname,
                "middlename": patient.profile.middlename,
                "hin": patient.hin,
            },
            **paginated_data
        })
        
class ListCreateSubaccountView(generics.ListCreateAPIView):
    serializer_class = CreateSubaccountSerializer
    
    def get_queryset(self):
        return Subaccount.objects.filter(parent=self.request.user).select_related("parent").order_by('-created_at')
    
class ListSubaccountMedicalRecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    
    def get_queryset(self):
        hin = self.kwargs.get("hin")
        
        if not hin:
            raise ValidationError("Subaccount hin should be provided")
        
        return MedicalRecord.objects.filter(patient__hin = hin).select_related("patient", "hospital").prefetch_related("drug_records", "attachments").order_by('-created_at')
    
class UpgradeSubaccount(generics.CreateAPIView):
    serializer_class = UpgradeSubaccountSerializer
    
    # def perform_create(self, serializer):
    #     user = serializer.save()
    #     otp = OTP.generate_otp(user)
        
    #     send_mail(
    #         subject="Verify your email",
    #         message=(
    #             f"Enter the OTP below into the required field \n"
    #             f"The OTP will expire in 10 mins\n\n"
    #             f"OTP: {otp}\n\n"
    #             f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
    #             f"From the Docuhealth Team"
    #         ),
    #         recipient_list=[user.email],
    #         from_email=None,
    #     )
    