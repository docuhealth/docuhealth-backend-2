from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.template.loader import render_to_string

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from docuhealth2.views import PublicGenericAPIView, BaseUserCreateView
from docuhealth2.utils.supabase import delete_from_supabase, upload_files, upload_file_to_supabase
from docuhealth2.utils.email_service import BrevoEmailService
from docuhealth2.authentications import ClientHeaderAuthentication
from docuhealth2.permissions import IsAuthenticatedHospitalAdmin, IsAuthenticatedHospitalStaff, IsAuthenticatedPatient, IsAuthenticatedPharmacyPartner

from .serializers import CreateHospitalSerializer, HospitalInquirySerializer, HospitalVerificationRequestSerializer, ApproveVerificationRequestSerializer, HospitalFullInfoSerializer, HospitalBasicInfoSerializer, SubscriptionPlanSerializer, SubscriptionSerializer, PharmacyRotateKeySerializer, CreatePharmacyPartnerSerializer, PharmacyOnboardingRequestSerializer, ListPharmacyOnboardingRequestSerializer, ApprovePharmacyOnboardingRequestSerializer, RotatePharmacyCodeSerializer

from .models import HospitalInquiry, HospitalVerificationRequest, VerificationToken, HospitalProfile, SubscriptionPlan, PharmacyProfile, Client

from .requests import create_customer, initialize_transaction

from accounts.models import User
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

import secrets

from organizations.models import Subscription


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
        
        uploaded_data = upload_files(documents, "hospital_verification_docs")
        
        try:
            print(request.data)   
            serializer = self.get_serializer(data={
                "inquiry": int(inquiry) if inquiry else None,
                "official_email": official_email, 
                "documents": uploaded_data, 
                "status": HospitalVerificationRequest.Status.PENDING, 
                "reviewed_by": user
            })
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            
        except Exception as e:
            for doc in uploaded_data:
                delete_from_supabase(doc['path'])
            
            print(f"Onboarding Error: {str(e)}")
            raise e
        
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
        serializer = self.get_serializer(request.user)
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
    permission_classes = [IsAuthenticatedPatient | IsAuthenticatedHospitalAdmin] #TODO: Change to docuhealth admin only
    
    def get_queryset(self):
        user_role = self.request.user.role
        return SubscriptionPlan.objects.filter(role__in=[user_role, "test"])
    
@extend_schema(tags=["Subscriptions"], summary="List subscription plans by role")
class ListSubscriptionPlansByRoleView(generics.ListAPIView):
    serializer_class = SubscriptionPlanSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedPatient | IsAuthenticatedHospitalAdmin]
    
    def get_queryset(self):
        role_param = self.kwargs.get("role")
        if role_param not in [User.Role.PATIENT, User.Role.HOSPITAL]:
            return SubscriptionPlan.objects.none()
        
        return SubscriptionPlan.objects.filter(role__in=[role_param, "test"])
    
@extend_schema(tags=["Subscriptions"])
class CreateSubscriptionView(generics.CreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticatedPatient | IsAuthenticatedHospitalAdmin] 
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context
    
    @transaction.atomic
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
        
@extend_schema(tags=["Pharmacy"], summary="Create a new pharmacy partner")
class CreatePharmacyPartnerView(PublicGenericAPIView, BaseUserCreateView):
    serializer_class = CreatePharmacyPartnerSerializer
    permission_classes = [permissions.AllowAny]
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save(is_active=True)
        
        raw_secret = f"dh_sk_{secrets.token_urlsafe(32)}" 
        client = Client.objects.create(
            user=user,
            client_secret_hash=make_password(raw_secret), 
        )
        
        context = {"partner_name": user.pharmacy_partner.name}
        html_content = render_to_string('emails/pharmacy_partner_onboarding.html', context)
        
        mailer.send(
            subject="Welcome to Docuhealth Services!",
            body=html_content,
            recipient=user.email,
            is_html=True
        )
        
        return Response({
            "status": "success",
            "message": "Pharmacy partner created successfully.",
            "data": {
                "client_id": client.client_id,
                "client_secret": raw_secret,
                "partner_name": user.pharmacy_partner.name
            }
        }, status=status.HTTP_201_CREATED)
        
@extend_schema(
    tags=["Pharmacy"],
    summary="Send an onboarding request for a pharmacy",
    description="Submit pharmacy details and verification documents. Use 'multipart/form-data' for file uploads.",
    parameters=[
        OpenApiParameter(
            name="X-Client-ID",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description="Your Partner Client ID",
            required=True,
        ),
        OpenApiParameter(
            name="X-Client-Secret",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description="Your Partner Secret Key",
            required=True,
        ),
    ],
    responses={
        201: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
    },
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string', 'minLength': 8},
                # Pharmacy Profile Fields (Flattened for the UI)
                'name': {'type': 'string', 'description': 'Pharmacy Business Name'},
                'license_no': {'type': 'string', 'description': 'Medical/Pharmacy License Number'},
                'phone': {'type': 'string'},
                'building_no': {'type': 'string'},
                'street': {'type': 'string'},
                'city': {'type': 'string'},
                'state': {'type': 'string'},
                'country': {'type': 'string'},
                'message': {'type': 'string', 'description': 'Optional note to admin'},
                # The File Upload Field
                'documents': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'binary'},
                    'description': 'One or more verification documents (PDF, JPG, PNG)'
                },
            },
            'required': ['email', 'password', 'name', 'license_no', 'phone', 'documents']
        }
    }
) 
class CreatePharmacyOnboardingRequest(PublicGenericAPIView, generics.CreateAPIView):
    authentication_classes = [ClientHeaderAuthentication]
    permission_classes = [permissions.AllowAny]
    serializer_class = PharmacyOnboardingRequestSerializer
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        documents = request.FILES.getlist('documents')
        email = request.data.get("email")
        password = request.data.get("password")
        
        profile_data = {
            'name': request.data.get('name'),
            'license_no': request.data.get('license_no'),
            'phone': request.data.get('phone'),
            'street': request.data.get('street'),
            'city': request.data.get('city'),
            'state': request.data.get('state'),
            'country': request.data.get('country'),
        }
        
        if request.data.get('building_no'):
            profile_data['building_no'] = request.data.get('building_no')
            
        if request.data.get('message'):
            profile_data['message'] = request.data.get('message')
            
        if not email:
            return Response({"detail": "Email is required", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({"detail": "Email already registered.", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(documents) == 0:
            return Response({"detail": "At least one verification document is required", "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_data = upload_files(documents, "pharmacy_verification_docs")
        profile_data['documents'] = uploaded_data
                    
        try:
            serializer = self.get_serializer(data={"email": email, "profile": profile_data, "password": password})
            serializer.is_valid(raise_exception=True)
        
            partner = request.user.pharmacy_partner
            user = User.objects.create(email=email, password=password, role=User.Role.PHARMACY, is_active=False)
            PharmacyProfile.objects.create(user=user, partner=partner, **profile_data)
            
            return Response({
                "status": "success",
                "message": "Onboarding request submitted. It is now awaiting admin approval."
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            for doc in uploaded_data:
                delete_from_supabase(doc['path'])
            
            print(f"Onboarding Error: {str(e)}")
            raise e
            
@extend_schema(
    tags=["Pharmacy"],
    summary="List Onboarded Pharmacies",
    description=(
        "Retrieves a list of all pharmacies onboarded by the authenticated partner. "
        "This allows partners to track the status (PENDING, APPROVED, REJECTED) "
        "and retrieve the PharmCode for approved pharmacies."
    ),
    parameters=[
        OpenApiParameter(
            name="X-Client-ID",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description="Partner Client ID",
            required=True,
        ),
        OpenApiParameter(
            name="X-Client-Secret",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description="Partner Secret Key",
            required=True,
        ),
    ],
    responses={
        200: ListPharmacyOnboardingRequestSerializer(many=True),
        401: OpenApiTypes.OBJECT,
    }
) 
class ListPharmacyOnboardingView(generics.ListAPIView):
    authentication_classes = [ClientHeaderAuthentication]
    queryset = PharmacyProfile.objects.all()
    serializer_class = ListPharmacyOnboardingRequestSerializer
    
    def get_queryset(self):
        partner = self.request.user.pharmacy_partner
        return PharmacyProfile.objects.filter(partner=partner).order_by('-created_at')

@extend_schema(tags=["Pharmacy"], summary="Get a pharmacy onboarding request") 
class RetrievePharmacyOnboardingRequest(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedPharmacyPartner]
    queryset = PharmacyProfile.objects.all()
    serializer_class = ListPharmacyOnboardingRequestSerializer
         
@extend_schema(tags=["Pharmacy DH Admin"], summary="Approve a pharmacy onboarding request") 
class ApprovePharmacyOnboardingRequestView(generics.GenericAPIView):
    queryset = PharmacyProfile.objects.filter(status=PharmacyProfile.Status.PENDING)
    serializer_class = ApprovePharmacyOnboardingRequestSerializer
    #TODO: Add permission classes of DH admin
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        pharmacy = validated_data.get('pharmacy_id')
        login_url = validated_data.get('login_url')
        
        pharmacy.status = PharmacyProfile.Status.APPROVED
        pharmacy.reviewed_at = timezone.now() 
        pharmacy.reviewed_by = request.user
        pharmacy.save(update_fields=["status", "reviewed_at", "reviewed_by", "pharm_code"])
        
        pharmacy_user = pharmacy.user
        pharmacy_user.is_active = True
        pharmacy_user.save(update_fields=["is_active"])
        
        pharmacy_context = {
            'pharmacy_name': pharmacy.name,
            'pharm_code': pharmacy.pharm_code,
            'login_url': login_url,
        }
        partner_context = {
            'pharmacy_name': pharmacy.name,
             'pharm_code': pharmacy.pharm_code,
        }

        pharmacy_html_content = render_to_string('emails/pharmacy_approval_email.html', pharmacy_context)
        partner_html_content = render_to_string('emails/partner_pharmacy_approval.html', partner_context)
            
        mailer.send(
            subject = 'Welcome to DocuHealth - Your Pharmacy Account is Ready',
            body = pharmacy_html_content,
            recipient = pharmacy.user.email,
            is_html = True
        )
        
        mailer.send(
            subject = 'Pharmacy Approved',
            body = partner_html_content,
            recipient = pharmacy.partner.user.email,
            is_html = True
            
        )

        return Response({
            "status": "success",
            "message": "Pharmacy approved and credentials generated.",
            "data": {
                "pharm_code": pharmacy.pharm_code,
                "business_name": pharmacy.name
            }
        }, status=status.HTTP_201_CREATED)

@extend_schema(
    tags=["Pharmacy"],
    summary="Rotate API Secret",
    description=(
        "Invalidates the current client_secret and generates a new one. "
        "The old secret will stop working immediately. This action requires "
        "the partner's account password for verification."
    ),
    request=PharmacyRotateKeySerializer,
    responses={
        200: OpenApiExample(
            'Success Response',
            value={
                "status": "success",
                "message": "Keys rotated successfully.",
                "data": {
                    "client_id": "uuid-string",
                    "new_client_secret": "dh_sk_..."
                }
            }
        ),
        403: OpenApiExample('Auth Error', value={"detail": "Invalid password."})
    }
)
class PharmacyPartnerRotateKeyView(generics.GenericAPIView): #TODO: Add audit
    # authentication_classes = [ClientHeaderAuthentication]
    permission_classes = [IsAuthenticatedPharmacyPartner]
    serializer_class = PharmacyRotateKeySerializer

    def post(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        current_password = serializer.validated_data.get('password')
        if not current_password or not user.check_password(current_password):
            return Response({"detail": "Security verification failed. Invalid password."}, status=status.HTTP_403_FORBIDDEN)

        client = user.client
        new_raw_secret = f"dh_sk_{secrets.token_urlsafe(32)}"
        
        client.client_secret_hash = make_password(new_raw_secret)
        client.save(update_fields=['client_secret_hash'])

        return Response({
            "status": "success",
            "message": "Keys rotated successfully. Update your environment variables immediately.",
            "data": {
                "client_id": client.client_id,
                "new_client_secret": new_raw_secret
            }
        }, status=status.HTTP_200_OK)

@extend_schema(
    tags=["Pharmacy"],
    summary="Rotate PharmCode Identifier",
    description=(
        "Generates a brand new PharmCode for the pharmacy. "
        "The old PharmCode will become invalid immediately. "
        "This action is typically taken if the current code has been compromised or during a rebranding."
    ),
    parameters=[
        OpenApiParameter("X-Client-ID", OpenApiTypes.STR, location=OpenApiParameter.HEADER, required=True),
        OpenApiParameter("X-Client-Secret", OpenApiTypes.STR, location=OpenApiParameter.HEADER, required=True),
    ],
    responses={
        200: OpenApiExample(
            'Successful Rotation',
            value={
                "status": "success",
                "message": "PharmCode rotated successfully",
                "data": {
                    "old_code": "PHARM-A1B2",
                    "new_code": "PHARM-F5G9"
                }
            }
        )
    }
)
class RotatePharmacyCodeView(generics.GenericAPIView):
    # authentication_classes = [ClientHeaderAuthentication]
    permission_classes = [IsAuthenticatedPharmacyPartner]
    serializer_class = RotatePharmacyCodeSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        
        pharmacy = validated_data.get("old_code")
        old_code = pharmacy.pharm_code
        new_code = f"PHARM-{secrets.token_hex(4).upper()}"
        
        while PharmacyProfile.objects.filter(pharm_code=new_code).exists():
            new_code = f"PHARM-{secrets.token_hex(4).upper()}"
        
        pharmacy.pharm_code = new_code
        pharmacy.save(update_fields=['pharm_code'])

        # TODO: Add audit
        print(f"IDENTITY ROTATION: {pharmacy.name} changed from {old_code} to {new_code}")
        
        context = {
            "pharmacy_name": pharmacy.name,
            "old_pharm_code": old_code,
            "new_pharm_code": new_code
        }
        pharmacy_html_content = render_to_string('emails/pharmacy_code_change_email.html', context)
        
        mailer.send(
            subject="Pharmacy Code Rotation",
            html_content=pharmacy_html_content,
            recipient=pharmacy.user.email,
            is_html=True
        )

        return Response({
            "status": "success",
            "message": "A new PharmCode has been generated.",
            "data": {
                "old_code": old_code,
                "new_code": new_code
            }
        }, status=status.HTTP_200_OK)

@extend_schema(tags=["Pharmacy DH Admin"], summary="Get Pharmacy Partner Client Info")  
class GetPharmacyPartnerClientInfo(generics.GenericAPIView):
    # authentication_classes = [ClientHeaderAuthentication]
    permission_classes = [IsAuthenticatedPharmacyPartner]

    def get(self, request, *args, **kwargs):
        user = request.user  
        client = user.client
        partner = user.pharmacy_partner
        
        client_id = client.client_id
        partner_name = partner.name
        return Response({"client_id": client_id, "partner_name": partner_name}, status=status.HTTP_200_OK)


        
        
    