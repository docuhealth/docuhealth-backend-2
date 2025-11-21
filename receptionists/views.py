from django.shortcuts import render
from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound

from drf_spectacular.utils import extend_schema

from docuhealth2.permissions import IsAuthenticatedReceptionist
from docuhealth2.utils.email_service import BrevoEmailService

from .serializers import  BookAppointmentSerializer

from hospitals.models import HospitalPatientActivity, HospitalStaffProfile, WardBed, Admission
from hospitals.serializers import HospitalActivitySerializer, HospitalAppointmentSerializer, HospitalStaffProfileSerializer, AdmissionSerializer, HospitalStaffInfoSerilizer

from appointments.models import Appointment

from patients.serializers import PatientSerializer, PatientProfileSerializer

from core.models import User, OTP
from core.serializers import UpdatePasswordSerializer

mailer = BrevoEmailService()

@extend_schema(tags=["Receptionist"])
class ReceptionistDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedReceptionist]

    def get(self, request, *args, **kwargs):
        staff = request.user.hospital_staff_profile
        hospital = staff.hospital

        receptionist_info = HospitalStaffInfoSerilizer(staff).data

        recent_qs = (
            HospitalPatientActivity.objects.filter(hospital=hospital).select_related("patient", "staff").order_by("-created_at"))

        recent_page = self.paginate_queryset(recent_qs)
        recent_serializer = HospitalActivitySerializer(recent_page, many=True)
        recent_paginated = self.get_paginated_response(recent_serializer.data).data

        upcoming_qs = (
            Appointment.objects.filter(hospital=hospital, status="pending").select_related("patient").order_by("scheduled_time"))

        upcoming_page = self.paginate_queryset(upcoming_qs)
        upcoming_serializer = HospitalAppointmentSerializer(upcoming_page, many=True)
        upcoming_paginated = self.get_paginated_response(upcoming_serializer.data).data

        return Response({
            "receptionist": receptionist_info,
            "recent_patients": recent_paginated,
            "upcoming_appointments": upcoming_paginated
        }, status=status.HTTP_200_OK)
        
@extend_schema(tags=["Receptionist"])
class CreatePatientView(generics.CreateAPIView):
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticatedReceptionist]
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        
        existing_inactive_user = User.objects.filter(email=email, is_active=False).first()
        if existing_inactive_user:
            existing_inactive_user.delete()  

        return super().post(request, *args, **kwargs)
    
    @transaction.atomic
    def perform_create(self, serializer):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        user = serializer.save()
        otp = OTP.generate_otp(user, expiry_minutes=60)
        
        mailer.send(
            subject="Verify your email",
            body=(
                f"Enter the OTP below into the required field \n"
                f"The OTP will expire in 10 mins\n\n"
                f"OTP: {otp}\n\n"
                f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
                f"From the Docuhealth Team"
            ),
            recipient=user.email,
        )
        
        HospitalPatientActivity.objects.create(patient=user.patient_profile, staff=staff, hospital=hospital, action="create_patient_account")
        
@extend_schema(tags=["Receptionist"])
class GetPatientDetailsView(generics.RetrieveAPIView):
    serializer_class = PatientProfileSerializer
    lookup_url_kwarg = "hin"
    permission_classes = [IsAuthenticatedReceptionist]
    
    def get_object(self):
        hin = self.kwargs.get(self.lookup_url_kwarg)

        try:
            return User.objects.filter(role=User.Role.PATIENT).select_related("patient_profile").get(patient_profile__hin=hin)
        
        except User.DoesNotExist:
            raise NotFound({"detail": "Patient with this HIN does not exist."})
        
    def get(self, request, *args, **kwargs):
        patient_user = self.get_object()
        staff = request.user.hospital_staff_profile
        hospital = staff.hospital
        
        serializer = self.get_serializer(patient_user)
        
        HospitalPatientActivity.objects.create(patient=patient_user.patient_profile, staff=staff, hospital=hospital, action="check_patient_info")
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Receptionist"])
class GetStaffByRoleView(generics.ListAPIView):
    serializer_class = HospitalStaffProfileSerializer
    pagination_class = None
    
    def get(self, request, *args, **kwargs):
        staff_role = kwargs.get("role")
        hospital = request.user.hospital_staff_profile.hospital
        
        if not staff_role:
            return Response({"detail": "staff_role is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not staff_role in ["doctor", "nurse"]:
            return Response({"detail": "staff_role is invalid. Can only be 'doctor' or 'nurse'"}, status=status.HTTP_400_BAD_REQUEST)
        
        staff_qs = HospitalStaffProfile.objects.filter(role=staff_role, hospital=hospital).select_related("hospital")
        
        return Response(self.get_serializer(staff_qs, many=True).data, status=status.HTTP_200_OK)

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
        
@extend_schema(tags=['Receptionist'], summary="Request admission for a patient")
class RequestAdmissionView(generics.CreateAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedReceptionist]
    
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
    
@extend_schema(tags=["Receptionist"], summary="List all admission requests that are pending")
class ListAdmissionRequestsView(generics.ListAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedReceptionist]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        
        return Admission.objects.filter(hospital=hospital, status=Admission.Status.PENDING).order_by('request_date')