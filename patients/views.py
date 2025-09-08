from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from medicalrecords.serializers import MedicalRecordSerializer
from medicalrecords.models import MedicalRecord

from .models import Subaccount
from .serializers import SubaccountSerializer

from docuhealth2.views import PaginatedView

class PatientDashboardView(generics.GenericAPIView, PaginatedView):
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
        
class CreateSubaccountView(generics.CreateAPIView):
    serializer_class = SubaccountSerializer
    queryset = Subaccount.objects.all().order_by('-created_at')
    
    def get_queryset(self):
        return Subaccount.objects.filter(parent=self.request.user).select_related("parent")
    
    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)
    