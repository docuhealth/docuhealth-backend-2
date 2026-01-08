from rest_framework import generics
from rest_framework.exceptions import  ValidationError

from docuhealth2.permissions import IsAuthenticatedHospitalAdmin, IsAuthenticatedHospitalStaff

from drf_spectacular.utils import extend_schema

from models import HospitalWard, WardBed
from .serializers  import WardSerializer, WardBedSerializer

from accounts.models import User

@extend_schema(tags=["Hospital"])
class ListCreateWardsView(generics.ListCreateAPIView):
    serializer_class = WardSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin | IsAuthenticatedHospitalStaff]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.HOSPITAL:
            hospital = self.request.user.hospital_profile
        else:
            hospital = self.request.user.hospital_staff_profile.hospital
            
        return HospitalWard.objects.filter(hospital=hospital).order_by('created_at')
    
    def perform_create(self, serializer):
        user = self.request.user
        
        if user.role == User.Role.HOSPITAL:
            hospital = self.request.user.hospital_profile
        else:
            hospital = self.request.user.hospital_staff_profile.hospital
            
        ward = serializer.save(hospital=hospital)
        
        for num in range(1, ward.total_beds + 1):
            WardBed.objects.create(
                ward=ward,
                bed_number=str(num)
            )
        
@extend_schema(tags=["Hospital Admin"], summary="Retrieve(get), update(patch) or delete(delete) a specific ward")
class RetrieveUpdateDeleteWardView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WardSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin | IsAuthenticatedHospitalStaff]
    http_method_names = ["get", "patch", "delete"]
    
    def get_queryset(self):
        return HospitalWard.objects.filter(hospital=self.request.user.hospital_profile)

@extend_schema(tags=["Hospital"])
class ListBedsByWardView(generics.ListAPIView):
    serializer_class = WardBedSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin | IsAuthenticatedHospitalStaff]
    pagination_class = None
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.HOSPITAL:
            hospital = self.request.user.hospital_profile
        else:
            hospital = self.request.user.hospital_staff_profile.hospital
            
        ward_id = self.kwargs["ward_id"]
        
        if not ward_id:
            raise ValidationError("Ward ID should be provided")
        
        ward = HospitalWard.objects.filter(id=ward_id, hospital=hospital).first()
        if not ward:
            raise ValidationError("Ward with the provided ID not found")
        
        return WardBed.objects.filter(ward=ward).order_by('bed_number')