from django.db import transaction
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from drf_spectacular.utils import extend_schema

from docuhealth2.permissions import IsAuthenticatedNurse

from .serializers import  AssignAppointmentToDoctorSerializer

from hospitals.models import  WardBed, Admission, VitalSignsRequest
from hospitals.serializers.services import  HospitalAppointmentSerializer, AdmissionSerializer, WardBasicInfoSerializer, VitalSignsRequestSerializer, VitalSignsSerializer, HospitalStaffInfoSerilizer

from appointments.models import Appointment

@extend_schema(tags=["Nurse"], summary='Nurse Dashboard')
class NurseDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedNurse]

    def get(self, request, *args, **kwargs):
        staff = request.user.hospital_staff_profile
        hospital = staff.hospital
        ward = staff.ward

        response = {}
        
        nurse_info = HospitalStaffInfoSerilizer(staff).data
        response['nurse'] = nurse_info
        
        if ward:
            ward_info = WardBasicInfoSerializer(ward).data
            response['ward_info'] = ward_info

        return Response(response, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Nurse"], summary="Get admissions to Nurse' ward")
class ListAdmissionsView(generics.ListAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    def get_queryset(self):
        user = self.request.user
        staff = user.hospital_staff_profile
        hospital = staff.hospital
        ward = staff.ward
        
        if not ward:
            raise ({"details": "Nurse is not assigned to any ward"})
        
        return Admission.objects.filter(hospital=hospital, ward=ward, status=Admission.Status.ACTIVE).select_related("patient", "staff", "hospital", "ward").order_by("-admission_date")
    
@extend_schema(tags=["Nurse"], summary="List all admission requests to nurses ward")
class ListAdmissionRequestsView(generics.ListAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        ward = staff.ward
        
        return Admission.objects.filter(hospital=hospital, ward=ward, status=Admission.Status.PENDING).order_by('request_date')
    
@extend_schema(tags=["Nurse"], summary="List all vital signs request to nurse")
class ListVitalSignsRequest(generics.ListAPIView):
    serializer_class = VitalSignsRequestSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        return VitalSignsRequest.objects.filter(staff=staff, status=VitalSignsRequest.Status.REQUESTED).select_related("staff").order_by("-created_at")
    
@extend_schema(tags=["Nurse"], summary="Process a vital signs request")
class ProcessVitalSignsRequestView(generics.CreateAPIView):
    serializer_class = VitalSignsSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    @transaction.atomic()
    def perform_create(self, serializer):
        vital_signs_request = serializer.validated_data.pop('request')
        patient = vital_signs_request.patient
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        serializer.save(patient=patient, staff=staff, hospital=hospital)
        
        vital_signs_request.processed_at = timezone.now()
        vital_signs_request.status = VitalSignsRequest.Status.PROCESSED
        vital_signs_request.save(update_fields=['processed_at', 'status'])
        
@extend_schema(tags=["Nurse"], summary="List appointments assigned to this nurse")
class ListAppointmentsView(generics.ListAPIView):
    serializer_class = HospitalAppointmentSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        return Appointment.objects.filter(staff=staff, status=Appointment.Status.PENDING).order_by('scheduled_time')
    
@extend_schema(tags=["Nurse"], summary="Assign appointment to a doctor")
class AssignAppointmentToDoctorView(generics.UpdateAPIView):
    serializer_class = AssignAppointmentToDoctorSerializer
    permission_classes = [IsAuthenticatedNurse]
    http_method_names = ['patch']
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        return Appointment.objects.filter(staff=staff, hospital=hospital)
    
