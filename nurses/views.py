from django.db import transaction
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from drf_spectacular.utils import extend_schema

from docuhealth2.permissions import IsAuthenticatedNurse

from .serializers import ConfirmAdmissionSerializer

from hospitals.models import HospitalPatientActivity, HospitalStaffProfile, WardBed, Admission, HospitalWard
from hospitals.serializers import HospitalActivitySerializer, HospitalAppointmentSerializer, HospitalStaffProfileSerializer, AdmissionSerializer, HospitalStaffStaffInfoSerilizer, WardBasicInfoSerializer


@extend_schema(tags=["Nurse"], summary='Nurse Dashboard')
class NurseDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedNurse]

    def get(self, request, *args, **kwargs):
        staff = request.user.hospital_staff_profile
        hospital = staff.hospital
        ward = staff.ward

        response = {}
        
        nurse_info = HospitalStaffStaffInfoSerilizer(staff).data
        response['nurse'] = nurse_info
        
        if ward:
            ward_info = WardBasicInfoSerializer(ward).data
            response['ward_info'] = ward_info

            admissions_qs = (
                Admission.objects.filter(hospital=hospital, ward=ward, status=Admission.Status.ACTIVE).select_related("patient", "staff", "hospital", "ward").order_by("-admission_date"))

            admissions_page = self.paginate_queryset(admissions_qs)
            admissions_serializer = AdmissionSerializer(admissions_page, many=True)
            admissions_paginated = self.get_paginated_response(admissions_serializer.data).data
            
            response['admissions'] = admissions_paginated

        return Response(response, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Nurse"], summary="List all admission requests to nurses ward")
class ListAdmissionRequestsView(generics.ListAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [IsAuthenticatedNurse]
    
    def get_queryset(self):
        staff = self.request.user.hospital_staff_profile
        hospital = staff.hospital
        ward = staff.ward
        
        return Admission.objects.filter(hospital=hospital, ward=ward, status=Admission.Status.PENDING).order_by('request_date')
    
@extend_schema(tags=['Nurse'], summary="Confirm admission of patient in a ward")
class ConfirmAdmissionView(generics.UpdateAPIView):
    serializer_class = ConfirmAdmissionSerializer
    permission_classes = [IsAuthenticatedNurse]
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