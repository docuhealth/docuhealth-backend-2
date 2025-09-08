from rest_framework import generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from medicalrecords.serializers import MedicalRecordSerializer
from medicalrecords.models import MedicalRecord

class PatientDashboardView(generics.GenericAPIView):
    serializer_class = MedicalRecordSerializer  
    pagination_class = PageNumberPagination
    pagination_class.page_size_query_param = 'size'
    pagination_class.max_page_size = 100

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
