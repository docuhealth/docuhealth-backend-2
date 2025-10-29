from django.core.mail import send_mail
from django.db import transaction

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from core.models import OTP
from docuhealth2.views import PublicGenericAPIView, BaseUserCreateView
from docuhealth2.permissions import IsAuthenticatedHospital
from docuhealth2.utils.supabase import upload_file_to_supabase

from drf_spectacular.utils import extend_schema

from .serializers import CreateHospitalSerializer, CreateDoctorSerializer, HospitalInquirySerializer, HospitalVerificationRequestSerializer, ApproveVerificationRequestSerializer
from .models import HospitalInquiry, HospitalVerificationRequest, VerificationToken

@extend_schema(tags=["Hospital"])  
class CreateHospitalView(BaseUserCreateView, PublicGenericAPIView):
    serializer_class = CreateHospitalSerializer
    
    def perform_create(self, serializer):
        user = serializer.save()
        otp = OTP.generate_otp(user)
        
        # send_mail(
        #     subject="Verify your email",
        #     message=(
        #         f"Enter the OTP below into the required field \n"
        #         f"The OTP will expire in 10 mins\n\n"
        #         f"OTP: {otp}\n\n"
        #         f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
        #         f"From the Docuhealth Team"
        #     ),
        #     recipient_list=[user.email],
        #     from_email=None,
        # )
        
@extend_schema(tags=["Hospital"])  
class CreateDoctorView(BaseUserCreateView):
    serializer_class = CreateDoctorSerializer
    permission_classes = [IsAuthenticatedHospital]
    
    def perform_create(self, serializer):
        user = serializer.save()
        otp = OTP.generate_otp(user)
        
        # send_mail(
        #     subject="Verify your email",
        #     message=(
        #         f"Enter the OTP below into the required field \n"
        #         f"The OTP will expire in 10 mins\n\n"
        #         f"OTP: {otp}\n\n"
        #         f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
        #         f"From the Docuhealth Team"
        #     ),
        #     recipient_list=[user.email],
        #     from_email=None,
        # )
        
@extend_schema(tags=["Hospital"])
class ListCreateHospitalInquiryView(generics.ListCreateAPIView, PublicGenericAPIView):
    serializer_class = HospitalInquirySerializer
    queryset = HospitalInquiry.objects.all().order_by('-created_at')    
    
    def perform_create(self, serializer):
        redirect_url = serializer.validated_data.pop("redirect_url")
        inquiry = serializer.save(status=HospitalInquiry.Status.PENDING)

        print(redirect_url)
        # verification_link = f"{redirect_url}?inquiry_id={inquiry.id}"
         # TODO: Send verification link with inquiry id to contact_email

        inquiry.status = HospitalInquiry.Status.CONTACTED
        inquiry.save(update_fields=["status"])
        
        return Response({"detail": "Verification link sent successfully"}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Hospital"])
class ListCreateHospitalVerificationRequestView(generics.ListCreateAPIView, PublicGenericAPIView):
    queryset = HospitalVerificationRequest.objects.all()
    serializer_class = HospitalVerificationRequestSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request, *args, **kwargs):
        user = request.user
        documents = request.FILES.getlist('documents')
        
        inquiry = request.data.get("inquiry")
        official_email = request.data.get("official_email")
        
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

@extend_schema(tags=["Hospital"])
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
        
        # verification_token = VerificationToken.generate_token(verification_request)
        # verification_url = f"{redirect_url}?token={verification_token}&request_id={verification_request.id}"
        # TODO: Send verification URL to verification_email.official_email
        
        verification_request.status = HospitalVerificationRequest.Status.APPROVED
        verification_request_inquiry = verification_request.inquiry
        verification_request_inquiry.status = HospitalInquiry.Status.CLOSED
        
        verification_request.save(update_fields=["status"])
        verification_request_inquiry.save(update_fields=["status"])
        
        return Response({"detail": "Hospital verified successfully"}, status=status.HTTP_200_OK)
    