from django.db import transaction

from rest_framework import generics

from docuhealth2.permissions import IsAuthenticatedHospitalAdmin, IsAuthenticatedHospitalStaff, IsAuthenticatedNurse, IsAuthenticatedDoctor, IsAuthenticatedPatient, IsAuthenticatedReceptionist
from docuhealth2.utils.email_service import BrevoEmailService

from .models import Appointment, HospitalPatientActivity
from .serializers import HospitalAppointmentSerializer, AssignAppointmentToDoctorSerializer, HospitalActivitySerializer, HospitalAppointmentSerializer, BookAppointmentSerializer

from drf_spectacular.utils import extend_schema

from accounts.models import User

mailer = BrevoEmailService()

@extend_schema(tags=["Hospital"], summary="List all appointments for the hospital")
class ListAllAppointmentsView(generics.ListAPIView):
    serializer_class = HospitalAppointmentSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin | IsAuthenticatedHospitalStaff]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.HOSPITAL:
            hospital = user.hospital_profile
        else:
            hospital = user.hospital_staff_profile.hospital
            
        return Appointment.objects.filter(hospital=hospital).order_by('scheduled_time')
    
@extend_schema(tags=["Nurse, Doctor"], summary="List appointments assigned to this staff")
class ListAppointmentsForStaffView(generics.ListAPIView):
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
    
@extend_schema(tags=["Patient"], summary="List appointments for the patient")
class ListPatientAppointmentsView(generics.ListAPIView):
    serializer_class = HospitalAppointmentSerializer
    permission_classes = [IsAuthenticatedPatient]
    
    def get_queryset(self):
        user = self.request.user
        
        return Appointment.objects.filter(patient=user.patient_profile).select_related("hospital").order_by('-scheduled_time')
    
@extend_schema(tags=["Receptionist"], summary="List recent patient activity on receptionist dashboard")
class ListRecentPatientsView(generics.ListAPIView):
    serializer_class = HospitalActivitySerializer
    permission_classes = [IsAuthenticatedReceptionist]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        return HospitalPatientActivity.objects.filter(hospital=hospital).select_related("patient", "staff").order_by("-created_at")
    
@extend_schema(tags=["Receptionist"], summary="List upcoming appointments on receptionist dashboard")
class ListUpcomingAppointmentsView(generics.ListAPIView):
    serializer_class = HospitalAppointmentSerializer
    permission_classes = [IsAuthenticatedReceptionist]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        return Appointment.objects.filter(hospital=hospital, status="pending").select_related("patient").order_by("scheduled_time")
    
@extend_schema(tags=["Receptionist"], summary="Book an appointment for a patient")
class BookAppointmentView(generics.CreateAPIView):
    serializer_class = BookAppointmentSerializer
    permission_classes = [IsAuthenticatedReceptionist]
    
    @transaction.atomic
    def perform_create(self, serializer):
        appointment = serializer.save(hospital=self.request.user.hospital_staff_profile.hospital)
        
        patient = appointment.patient
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        HospitalPatientActivity.objects.create(patient=patient, staff=staff, hospital=hospital, action="book_appointment")