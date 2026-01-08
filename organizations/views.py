from django.db import transaction
from django.db.models import Q

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from docuhealth2.views import PublicGenericAPIView, BaseUserCreateView
from docuhealth2.permissions import IsAuthenticatedHospitalAdmin, IsAuthenticatedHospitalStaff, IsAuthenticatedPatient
from docuhealth2.utils.supabase import upload_file_to_supabase
from docuhealth2.utils.email_service import BrevoEmailService

from drf_spectacular.utils import extend_schema

from .serializers import CreateHospitalSerializer, HospitalInquirySerializer, HospitalVerificationRequestSerializer, ApproveVerificationRequestSerializer, HospitalFullInfoSerializer, HospitalBasicInfoSerializer, SubscriptionPlanSerializer, SubscriptionSerializer
from .models import HospitalInquiry, HospitalVerificationRequest, VerificationToken, HospitalProfile, SubscriptionPlan
from .requests import create_customer, initialize_transaction

from accounts.models import User

mailer = BrevoEmailService()

@extend_schema(tags=["Hospital Onboarding"])  
class CreateHospitalView(PublicGenericAPIView, BaseUserCreateView):
    serializer_class = CreateHospitalSerializer
    
    def perform_create(self, serializer):
        login_url = serializer.validated_data.pop("login_url")
        user = serializer.save(is_active=True)
        
        mailer.send(
            subject="Verify your email",
            body=(
                f"Welcome to Docuhealth! \n\n"
                f"You have successfully created your Docuhealth account. \n\n"
                
                f"Please use the link below to log in to your account: \n\n"
                f"{login_url}\n\n"
                
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
            "status": HospitalVerificationRequest.Status.PENDING, 
            "reviewed_by": user
        })
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@extend_schema(tags=["Hospital Onboarding"])
class ApproveVerificationRequestView(PublicGenericAPIView, generics.GenericAPIView):
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
class GetHospitalInfo(generics.GenericAPIView):
    serializer_class = HospitalFullInfoSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin]

    def get(self, request, *args, **kwargs):
        user = request.user  
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
@extend_schema(tags=['Hospital', 'Doctor'], summary="Get all hospitals")
class ListHospitalsView(generics.ListAPIView):
    queryset = HospitalProfile.objects.all().select_related("user").order_by('name')
    serializer_class = HospitalBasicInfoSerializer
    permission_classes = [IsAuthenticatedHospitalStaff | IsAuthenticatedHospitalAdmin]
    
@extend_schema(tags=["Subscriptions"])
class ListCreateSubscriptionPlanView(generics.ListCreateAPIView):
    serializer_class = SubscriptionPlanSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedPatient | IsAuthenticatedHospitalAdmin] 
    
    def get_queryset(self):
        user_role = self.request.user.role
        return SubscriptionPlan.objects.filter(role=user_role)
    
@extend_schema(tags=["Subscriptions"])
class CreateSubscriptionView(generics.CreateAPIView):
        serializer_class = SubscriptionSerializer
        permission_classes = [IsAuthenticatedPatient | IsAuthenticatedHospitalAdmin] 
        
        def get_serializer_context(self):
            context = super().get_serializer_context()
            context["user"] = self.request.user
            return context
        
        def create(self, request, *args, **kwargs):
            user = request.user
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save()
            
            plan = subscription.plan
            paystack_cus_code = user.paystack_cus_code
            email = user.email
            
            if not paystack_cus_code:
                paystack_cus_code = create_customer({"email": email})
                user.paystack_cus_code = paystack_cus_code
                user.save(update_fields=['paystack_cus_code'])
                
            transaction_payload = {
                "email": email,
                "amount": plan.price * 100,
                "plan": plan.paystack_plan_code 
            }
            
            auth_url = initialize_transaction(transaction_payload)
            
            response_data = self.get_serializer(subscription).data
            response_data["authorization_url"] = auth_url
            return Response(response_data, status=status.HTTP_201_CREATED) 
