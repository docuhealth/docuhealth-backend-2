from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string

from concurrent.futures import ThreadPoolExecutor

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from docuhealth2.views import PublicGenericAPIView, BaseUserCreateView
from docuhealth2.permissions import IsAuthenticatedHospitalAdmin, IsAuthenticatedHospitalStaff, IsAuthenticatedPatient
from docuhealth2.utils.supabase import upload_file_to_supabase, delete_from_supabase
from docuhealth2.utils.email_service import BrevoEmailService

from drf_spectacular.utils import extend_schema

from .serializers import CreateHospitalSerializer, HospitalInquirySerializer, HospitalVerificationRequestSerializer, ApproveVerificationRequestSerializer, HospitalFullInfoSerializer, HospitalBasicInfoSerializer, SubscriptionPlanSerializer, SubscriptionSerializer, PharmacyOnboardingRequestSerializer, ApprovePharmacyOnboardingRequestSerializer
from .models import HospitalInquiry, HospitalVerificationRequest, VerificationToken, HospitalProfile, SubscriptionPlan, PharmacyOnboardingRequest, PharmacyProfile, PharmacyClient
from .requests import create_customer, initialize_transaction

from accounts.models import User

import uuid
import secrets

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
        
    
@extend_schema(tags=["Pharmacy"], summary="Send an onboarding request for a pharmacy")    
class CreatePharmacyOnboardingRequest(PublicGenericAPIView, generics.CreateAPIView):
    serializer_class = PharmacyOnboardingRequestSerializer
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        documents = request.FILES.getlist('documents')
        official_email = request.data.get("official_email")
        files_data = []
        uploaded_data = []
        
        if not official_email:
            return Response({"detail": "Official email is required", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=official_email).exists():
            return Response({"detail": "Email already registered.", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        if PharmacyOnboardingRequest.objects.filter(official_email=official_email).exists():
            return Response({"detail": "An onboarding request with this email has already been submitted. Contact admin.", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(documents) == 0:
            return Response({"detail": "Verification documents are required", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        for doc in documents:
            files_data.append({
                "bytes": doc.read(),
                "name": doc.name,
                "type": doc.content_type
            })
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = futures = [
                executor.submit(
                    upload_file_to_supabase, 
                    file['bytes'], file['name'], file['type'], 
                    "pharmacy_verification_docs"
                ) for file in files_data
            ]
            
            try:
                for future in futures:
                    result = future.result()
                    uploaded_data.append(result)
                    
                serializer = self.get_serializer(data={**request.data.dict(), "documents": uploaded_data})
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

            except Exception as e:
                for doc in uploaded_data:
                    delete_from_supabase(doc['path'])
                
                print(f"Onboarding Error: {str(e)}")
                raise e
@extend_schema(tags=["Pharmacy"], summary="Get all pharmacy onboarding requests")   
class ListPharmacyOnboardingRequest(generics.ListAPIView):
    queryset = PharmacyOnboardingRequest.objects.all()
    serializer_class = PharmacyOnboardingRequestSerializer

@extend_schema(tags=["Pharmacy"], summary="Get a pharmacy onboarding request") 
class RetrievePharmacyOnboardingRequest(generics.RetrieveAPIView):
    queryset = PharmacyOnboardingRequest.objects.all()
    serializer_class = PharmacyOnboardingRequestSerializer
         
@extend_schema(tags=["Pharmacy"], summary="Approve a pharmacy onboarding request") 
class ApprovePharmacyOnboardingRequestView(generics.GenericAPIView):
    queryset = PharmacyOnboardingRequest.objects.filter(status=PharmacyOnboardingRequest.Status.PENDING)
    serializer_class = ApprovePharmacyOnboardingRequestSerializer
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        onboarding = validated_data.get('request')
        
        if onboarding.status != PharmacyOnboardingRequest.Status.PENDING:
            return Response({"detail": "This request is already processed."}, status=400)
        
        password = validated_data.get('password')
        house_no = validated_data.get('house_no')
        login_url = validated_data.get('login_url')
        
        if house_no:
            street = f'{house_no}, {validated_data.get('street')}'
        
        user = User.objects.create(
            email = onboarding.official_email,
            role = User.Role.PHARMACY,
            password = password
        )

        profile = PharmacyProfile.objects.create(
            user=user, 
            request=onboarding,
            name=onboarding.name,
            street=street,
            city=validated_data.get('city'),
            state=validated_data.get('state'),
            country=validated_data.get('country'),
        )

        raw_secret = f"dh_sk_{secrets.token_urlsafe(32)}" 
        
        client = PharmacyClient.objects.create(
            pharmacy=profile,
            client_secret_hash=make_password(raw_secret), 
        )

        onboarding.status = PharmacyOnboardingRequest.Status.APPROVED
        onboarding.reviewed_at = timezone.now() 
        onboarding.reviewed_by = request.user
        onboarding.save(update_fields=["status", "reviewed_at", "reviewed_by"])
        
        context = {
            'pharmacy_name': profile.name,
            'login_url': login_url,
        }

        html_content = render_to_string('emails/pharmacy_approval_email.html', context)
            
        mailer.send(
            subject = 'Welcome to DocuHealth - Your Pharmacy Account is Ready',
            body = html_content,
            recipient = onboarding.official_email,
            is_html = True
        )

        return Response({
            "status": "success",
            "message": "Pharmacy approved and credentials generated.",
            "data": {
                "pharm_code": profile.pharm_code,
                "client_id": client.client_id,
                "client_secret": raw_secret,
                "business_name": profile.name
            }
        }, status=status.HTTP_201_CREATED)