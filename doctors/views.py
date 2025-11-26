from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser

from docuhealth2.views import PublicGenericAPIView, BaseUserCreateView
from docuhealth2.permissions import IsAuthenticatedHospitalAdmin, IsAuthenticatedHospitalStaff, IsAuthenticatedDoctor
from docuhealth2.utils.supabase import upload_file_to_supabase
from docuhealth2.utils.email_service import BrevoEmailService

from drf_spectacular.utils import extend_schema

from hospitals.serializers.services import VitalSignsRequestSerializer

@extend_schema(tags=["Doctor"])
class RequestVitalSignsView(generics.CreateAPIView):
    serializer_class = VitalSignsRequestSerializer
    permission_classes = [IsAuthenticatedDoctor]
    
    def perform_create(self, serializer):
        hospital = self.request.user.hospital_staff_profile.hospital
        return serializer.save(hospital=hospital)
    