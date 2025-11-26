from django.db import transaction
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser

from docuhealth2.views import PublicGenericAPIView, BaseUserCreateView
from docuhealth2.permissions import IsAuthenticatedHospitalAdmin, IsAuthenticatedHospitalStaff, IsAuthenticatedDoctor
from docuhealth2.utils.supabase import upload_file_to_supabase
from docuhealth2.utils.email_service import BrevoEmailService

from drf_spectacular.utils import extend_schema

from .serializers import PatientMedInfoSerializer
from hospitals.serializers.services import VitalSignsRequestSerializer, HospitalAppointmentSerializer, VitalSignsSerializer, AdmissionSerializer, ConfirmAdmissionSerializer
from patients.serializers import PatientFullInfoSerializer
from medicalrecords.serializers import DrugRecordSerializer, MedicalRecordSerializer

from medicalrecords.models import MedicalRecord
from appointments.models import Appointment
from hospitals.models import VitalSigns, WardBed, HospitalPatientActivity, Admission
from patients.models import PatientProfile
from medicalrecords.models import DrugRecord


@extend_schema(tags=["Doctor"])
class RequestVitalSignsView(generics.CreateAPIView):
    serializer_class = VitalSignsRequestSerializer
    permission_classes = [IsAuthenticatedDoctor]
    
    def perform_create(self, serializer):
        hospital = self.request.user.hospital_staff_profile.hospital
        return serializer.save(hospital=hospital)
    
@extend_schema(tags=["Doctor"], summary="List appointments assigned to this doctor")
class ListAppointmentsView(generics.ListAPIView):
    serializer_class = HospitalAppointmentSerializer
    permission_classes = [IsAuthenticatedDoctor]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        return Appointment.objects.filter(staff=staff, status=Appointment.Status.PENDING).order_by('scheduled_time')
    
@extend_schema(tags=["Doctor"], summary="List patients information")
class RetrievePatientInfoView(generics.RetrieveAPIView):
    serializer_class = PatientMedInfoSerializer
    lookup_field = "hin"
    queryset = PatientProfile.objects.all()

    def retrieve(self, request, *args, **kwargs):
        patient = self.get_object()

        latest_vitals = (VitalSigns.objects.filter(patient=patient).order_by('-created_at').first())

        ongoing_drugs = DrugRecord.objects.filter(patient=patient) # TODO: Add status

        data = {
            "patient_info": PatientFullInfoSerializer(patient).data,
            "latest_vitals": VitalSignsSerializer(latest_vitals).data if latest_vitals else None,
            "ongoing_drugs": DrugRecordSerializer(ongoing_drugs, many=True).data,
        }

        return Response(data)

@extend_schema(tags=["Doctor"], summary="Get patients medical records")
class ListPatientMedicalRecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticatedDoctor]

    def get_queryset(self):
        hin = self.kwargs.get("hin")
        
        try:
            patient = PatientProfile.objects.get(hin=hin)
        except PatientProfile.DoesNotExist:
            raise NotFound({"detail": "Patient not found"})

        return MedicalRecord.objects.filter(patient=patient).order_by('-created_at')
    
@extend_schema(tags=['Doctor'], summary="Request admission for a patient")
class RequestAdmissionView(generics.CreateAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedDoctor]
    
    @transaction.atomic
    def perform_create(self, serializer):
        admission = serializer.save(hospital=self.request.user.hospital_staff_profile.hospital)
        
        bed = admission.bed
        bed.status = WardBed.Status.REQUESTED
        bed.save(update_fields=["status"])
        
        patient = admission.patient
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        HospitalPatientActivity.objects.create(patient=patient, staff=staff, hospital=hospital, action="request_admission")
        
@extend_schema(tags=['Doctor'], summary="Confirm admission of patient in a ward")
class ConfirmAdmissionView(generics.UpdateAPIView):
    serializer_class = ConfirmAdmissionSerializer
    permission_classes = [IsAuthenticatedDoctor]
    lookup_url_kwarg = "admission_id"
    http_method_names = ['patch']
    
    def get_object(self):
        admission_id = self.kwargs[self.lookup_url_kwarg]
        staff = self.request.user.hospital_staff_profile

        try:
            return Admission.objects.get(id=admission_id, hospital=staff.hospital)
        
        except Admission.DoesNotExist:
            raise NotFound({"detail": "Admission not found."})
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        admission = self.get_object()

        serializer = self.get_serializer(data=request.data, context={"admission": admission, "request": request})
        serializer.is_valid(raise_exception=True)
        
        admission.status = Admission.Status.ACTIVE
        admission.admission_date = timezone.now()
        admission.save(update_fields=["status", "admission_date"])

        admission.bed.status = WardBed.Status.OCCUPIED
        admission.bed.save(update_fields=["status"])

        return Response({"detail": "Admission confirmed successfully."}, status=status.HTTP_200_OK)
    