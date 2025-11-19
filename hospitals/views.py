from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser

from docuhealth2.views import PublicGenericAPIView, BaseUserCreateView
from docuhealth2.permissions import IsAuthenticatedHospitalAdmin, IsAuthenticatedHospitalStaff
from docuhealth2.utils.supabase import upload_file_to_supabase
from docuhealth2.utils.email_service import BrevoEmailService

from appointments.models import Appointment

from drf_spectacular.utils import extend_schema

from .serializers import CreateHospitalSerializer, HospitalInquirySerializer, HospitalVerificationRequestSerializer, ApproveVerificationRequestSerializer, TeamMemberCreateSerializer, HospitalStaffProfileSerializer, RemoveTeamMembersSerializer, TeamMemberUpdateRoleSerializer, HospitalAppointmentSerializer, HospitalInfoSerializer, WardSerializer, WardBedSerializer

from .models import HospitalInquiry, HospitalVerificationRequest, VerificationToken, HospitalStaffProfile, HospitalWard, WardBed

from core.models import User

mailer = BrevoEmailService()

@extend_schema(tags=["Hospital Onboarding"])  
class CreateHospitalView(PublicGenericAPIView, BaseUserCreateView):
    serializer_class = CreateHospitalSerializer
    
    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        
        mailer.send(
            subject="Verify your email",
            body=(
                f"Welcome to Docuhealth! \n\n"
                f"You have successfully created your Docuhealth account. \n\n"
                
                f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
                f"From the Docuhealth Team"
            ),
            recipient=user.email,
        )
@extend_schema(tags=["Hospital Onboarding"])
class ListCreateHospitalInquiryView(PublicGenericAPIView, generics.ListCreateAPIView):
    serializer_class = HospitalInquirySerializer
    queryset = HospitalInquiry.objects.all().order_by('-created_at')    
    
    def perform_create(self, serializer):
        redirect_url = serializer.validated_data.pop("redirect_url")
        inquiry = serializer.save(status=HospitalInquiry.Status.PENDING)

        print(redirect_url)
        verification_link = f"{redirect_url}?inquiry_id={inquiry.id}"
        
        mailer.send(
            subject="Verify your hospital",
            body= (
                f"Welcome to Docuhealth! \n\n"
                f"Please click the link below to verify your hospital \n\n"
                
                f"{verification_link}\n\n"
                
                f"If you did not initiate this request, please contact support@docuhealthservices.com immediately\n\n"
                f"From the Docuhealth Team"
            ),
            recipient = inquiry.contact_email,
        )

        inquiry.status = HospitalInquiry.Status.CONTACTED
        inquiry.save(update_fields=["status"])
        
        return Response({"detail": "Verification link sent successfully"}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Hospital Onboarding"])
class ListCreateHospitalVerificationRequestView(PublicGenericAPIView, generics.ListCreateAPIView):
    queryset = HospitalVerificationRequest.objects.all()
    serializer_class = HospitalVerificationRequestSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request, *args, **kwargs):
        user = request.user
        documents = request.FILES.getlist('documents')
        
        inquiry = request.data.get("inquiry")
        official_email = request.data.get("official_email")
        
        if User.objects.filter(email=official_email).exists():
            return Response({"detail": "User with this official email already exists.", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(documents) == 0:
            return Response({"detail": "No documents provided", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        document_urls = []
        for document in documents:
            public_url = upload_file_to_supabase(document, "hospital_verification_docs")
            document_urls.append({
                "name": document.name,
                "url": public_url,
                "content_type": document.content_type,
            })
         
        print(request.data)   
        serializer = self.get_serializer(data={
            "inquiry": int(inquiry) if inquiry else None,
            "official_email": official_email, 
            "documents": document_urls, 
            status: HospitalVerificationRequest.Status.PENDING, 
            "reviewed_by": user
        })
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@extend_schema(tags=["Hospital Onboarding"])
class ApproveVerificationRequestView(generics.GenericAPIView):
    serializer_class = ApproveVerificationRequestSerializer
    
    @transaction.atomic  
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        verification_request = serializer.validated_data.get("verification_request")
        redirect_url = serializer.validated_data.get("redirect_url")
        print(redirect_url)
        
        if verification_request.status != HospitalVerificationRequest.Status.PENDING:
            return Response({"detail": "This verification request has already been processed"}, status=status.HTTP_400_BAD_REQUEST)
        
        verification_token = VerificationToken.generate_token(verification_request)
        onboarding_url = f"{redirect_url}?token={verification_token}&request_id={verification_request.id}"
        
        mailer.send(
            subject="Onboard your hospital",
            body = (
                f"Please click the link below to complete the onboarding process for your hospital \n\n"
                
                f"{onboarding_url}\n\n"
                
                f"If you did not initiate this request, please contact support@docuhealthservices.com immediately\n\n"
                f"From the Docuhealth Team"
            ),
            recipient=verification_request.official_email
        )
        
        verification_request.status = HospitalVerificationRequest.Status.APPROVED
        verification_request_inquiry = verification_request.inquiry
        verification_request_inquiry.status = HospitalInquiry.Status.CLOSED
        
        verification_request.save(update_fields=["status"])
        verification_request_inquiry.save(update_fields=["status"])
        
        return Response({"detail": "Hospital verified successfully"}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Hospital Admin"])  
class TeamMemberCreateView(generics.CreateAPIView):
    serializer_class = TeamMemberCreateSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin]
    
    @transaction.atomic
    def perform_create(self, serializer):
        hospital = self.request.user.hospital_profile
        invitation_message = serializer.validated_data.pop("invitation_message")
        user = serializer.save(is_active=True)
        
        mailer.send(
                subject=f"Welcome to {hospital.name} hospital",
                body=(
                    f"{invitation_message} \n\n"
                    f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
                    f"From the Docuhealth Team"
                ),
                recipient=user.email,
            )
        
@extend_schema(tags=["Hospital Admin"])
class TeamMemberListView(generics.ListAPIView):
    serializer_class = HospitalStaffProfileSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin]
    
    def get_queryset(self):
        return HospitalStaffProfile.objects.filter(hospital=self.request.user.hospital_profile).order_by('-created_at')
        
@extend_schema(tags=["Hospital Admin"])
class RemoveTeamMembersView(generics.GenericAPIView):
    serializer_class = RemoveTeamMembersSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin]
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        staff_ids = serializer.validated_data.get("staff_ids")
        hospital = request.user.hospital_profile

        users = HospitalStaffProfile.objects.filter(
            hospital=hospital,
            staff_id__in=staff_ids
        )
        
        found_ids = set(users.values_list("staff_id", flat=True))
        missing = set(staff_ids) - found_ids
        
        if missing:
            return Response({
                "staff_ids": [f"Invalid or unauthorized staff IDs: {', '.join(map(str, missing))}"]
            }, status=status.HTTP_400_BAD_REQUEST)

        user_ids = set(users.values_list("user_id", flat=True))

        updated_count = User.objects.filter(id__in=user_ids, is_active=True).update(is_active=False)
        if updated_count == 0:
            return Response(
                {"message": "No changes detected. No team members deactivated."},
                status=status.HTTP_200_OK
            )

        return Response(
            {"message": f"{updated_count} team member(s) deactivated successfully."},
            status=status.HTTP_200_OK
        )
        
@extend_schema(tags=["Hospital Admin"])
class TeamMemberUpdateRoleView(generics.UpdateAPIView):
    serializer_class = TeamMemberUpdateRoleSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin]
    http_method_names = ["patch"]
    
    def get_object(self):
        hospital = self.request.user.hospital_profile
        staff = HospitalStaffProfile.objects.filter(hospital=hospital, staff_id=self.kwargs["staff_id"]).first()
        
        if not staff:
            raise NotFound({"detail": "Staff not found or unauthorized."})
        
        return staff
    
@extend_schema(tags=["Hospital"])
class ListAppointmentsView(generics.ListAPIView):
    serializer_class = HospitalAppointmentSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin | IsAuthenticatedHospitalStaff]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.HOSPITAL:
            hospital = self.request.user.hospital_profile
        else:
            hospital = self.request.user.hospital_staff_profile.hospital
            
        return Appointment.objects.filter(hospital=hospital).order_by('scheduled_time')
    
@extend_schema(tags=["Hospital Admin"])
class GetHospitalInfo(generics.GenericAPIView):
    serializer_class = HospitalInfoSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin]

    def get(self, request, *args, **kwargs):
        user = request.user  
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
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