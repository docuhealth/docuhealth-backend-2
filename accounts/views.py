from django.db import transaction
from django.template.loader import render_to_string

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound

from drf_spectacular.utils import extend_schema

from .models import User, OTP, UserProfileImage, NINVerificationAttempt, PatientProfile, SubaccountProfile, HospitalStaffProfile, EmailChange

from .serializers import ForgotPasswordSerializer, VerifyOTPSerializer, ResetPasswordSerializer, UserProfileImageSerializer, UpdatePasswordSerializer, CreateSubaccountSerializer, UpgradeSubaccountSerializer, CreatePatientSerializer, UpdatePatientSerializer, GeneratePatientIDCardSerializer, GenerateSubaccountIDCardSerializer, VerifyUserNINSerializer, PatientBasicInfoSerializer, PatientEmergencySerializer, HospitalStaffInfoSerilizer, TeamMemberCreateSerializer, RemoveTeamMembersSerializer, TeamMemberUpdateRoleSerializer, ReceptionistCreatePatientSerializer, UpdateEmailSerializer, VerifyEmailOTPSerializer, UpdateProfileSerializer, UpdateHospitalAdminProfileSerializer

from docuhealth2.permissions import IsAuthenticatedHospitalAdmin, IsAuthenticatedHospitalStaff
from .requests import verify_nin_request
from .utils import *

from docuhealth2.views import PublicGenericAPIView
from docuhealth2.permissions import IsAuthenticatedHospitalStaff, IsAuthenticatedPatient, IsAuthenticatedDoctor, IsAuthenticatedNurse, IsAuthenticatedReceptionist
from docuhealth2.utils.email_service import BrevoEmailService

from records.serializers import MedicalRecordSerializer
from records.models import MedicalRecord

from facility.serializers import WardBasicInfoSerializer
from hospital_ops.models import HospitalPatientActivity
from accounts.serializers import PatientFullInfoSerializer
from organizations.models import Subscription

mailer = BrevoEmailService()

def set_refresh_cookie(response):
    data = response.data
    
    refresh = data.get("refresh")
    access = data.get("access")
    
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,    
        secure=True,      
        samesite="None"
    )

    response.data = {"data": {"access_token": access}, "detail": "Access granted", "status": "success"}
            
    return response

@extend_schema(tags=["Auth"])
class ListUserView(generics.ListAPIView):
    queryset = User.objects.exclude(role="subaccount").order_by("-created_at")
    serializer_class = PatientBasicInfoSerializer
      
@extend_schema(tags=["Auth"])  
class VerifySignupOTPView(PublicGenericAPIView):  
    serializer_class = VerifyOTPSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        valid, message = serializer.otp_instance.verify(serializer.otp)
        if not valid:
            return Response({"detail": message, "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.user.is_active = True
        serializer.user.save(update_fields=['is_active'])
        
        response = {"detail": f"Email verified successfully, proceed to login"}
        
        if serializer.user.role == User.Role.PATIENT:
            response["hin"] = serializer.user.patient_profile.hin
            
        return Response(response, status=status.HTTP_200_OK)

@extend_schema(tags=["Auth"])  
class LoginView(TokenObtainPairView, PublicGenericAPIView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        email = request.data.get("email")
        
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.get(email=email)
            role = user.role
            
            if role == User.Role.PATIENT:
                profile = user.patient_profile
                if not profile.nin_verified:
                    return Response({"detail": "NIN not verified. Kindly verify your NIN", "status": "error", "hin": profile.hin}, status=status.HTTP_403_FORBIDDEN)
            
            set_refresh_cookie(response)
            
            response.data["data"]["role"] = role
            
            if role == User.Role.HOSPITAL_STAFF:
                staff_profile = user.hospital_staff_profile
                hospital = staff_profile.hospital
                staff_role = staff_profile.role
                
                hospital_data = {
                    "name": hospital.name,
                    "hin": hospital.hin
                }
                
                response.data["data"]["hospital"] = hospital_data
                response.data["data"]["staff_role"] = staff_role
                
            if role in [User.Role.PATIENT, User.Role.HOSPITAL]:
                is_subscribed = Subscription.objects.filter(user=user, status=Subscription.SubscriptionStatus.ACTIVE).exists()
                response.data["data"]["is_subscribed"] = is_subscribed
                
            mailer.send(
                subject="New Login Alert",
                body = "There was a login attempt on your DOCUHEALTH account. If this was you, you can ignore this message. \n\nIf this was not you, please contact our support team at support@docuhealthservices.com \n\n\nFrom the Docuhealth Team",
                recipient=email,         
            )
                
        return response

@extend_schema(tags=["Auth"])  
class ForgotPassword(PublicGenericAPIView):
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        otp = OTP.generate_otp(serializer.user)
        print(otp)
        
        mailer.send(
            subject="Account Recovery",
            body = (
                        f"Enter the OTP below into the required field \n"
                        f"The OTP will expire in 10 mins\n\n"
                        f"OTP: {otp} \n\n"
                        f"If you did not iniate this request, please contact our support team at support@docuhealthservices.com   \n\n\n"
                        f"From the Docuhealth Team"
                    ),
            recipient=serializer.email,    
        )
        
        return Response({"detail": f"OTP sent successfully"}, status=status.HTTP_200_OK)

@extend_schema(tags=["Auth"])  
class VerifyForgotPasswordOTPView(PublicGenericAPIView):
    serializer_class = VerifyOTPSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        valid, message = serializer.otp_instance.verify(serializer.otp)
        if not valid:
            return Response({"detail": message, "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        access = AccessToken.for_user(serializer.user)

        response = Response({"data": {"access_token": str(access)}, "detail": "Access granted to reset password", "status": "success"}, status=status.HTTP_200_OK,)

        return response

@extend_schema(tags=["Auth"])  
class ResetPasswordView(GenericAPIView):
    serializer_class = ResetPasswordSerializer
    
    def patch(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_password = serializer.validated_data["new_password"]

        user = request.user
        user.set_password(new_password)
        user.save(update_fields=['password'])

        return Response({"detail": "Password reset successfully. Please log in with your new credentials.", "status": "success"}, status=200)

@extend_schema(tags=["Auth"])  
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        
        if not refresh_token:
            return Response({"detail": "Please login again"}, status=400)
        
        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        
        set_refresh_cookie(response)
        
        return response

@extend_schema(tags=["api"])  
class UploadUserProfileImageView(generics.CreateAPIView):
    serializer_class = UserProfileImageSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        user = self.request.user
        UserProfileImage.objects.filter(user=user).delete()
        serializer.save(user=user) 
        
@extend_schema(tags=['Auth'], summary="Update hospital staff or admin account password")
class UpdatePasswordView(generics.GenericAPIView):
    serializer_class = UpdatePasswordSerializer
    permission_classes = [IsAuthenticatedHospitalStaff | IsAuthenticatedHospitalAdmin]
    
    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.save(update_fields=['password'])

        return Response({"detail": "Password reset successfully. Please log in with your new credentials.", "status": "success"}, status=200)
   
@extend_schema(tags=["Auth"], summary="Verify user's NIN")   
class VerifyUserNINView(PublicGenericAPIView, generics.GenericAPIView):
    serializer_class = VerifyUserNINSerializer
    
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        nin = serializer.validated_data["nin"]
        patient_profile = serializer.validated_data["patient"]
        patient_profile = (PatientProfile.objects.select_for_update().get(id=patient_profile.id))
        
        user = patient_profile.user
        
        if patient_profile.nin_verified:
            return self._generate_login_response(user)
        
        nin_hash = hash_nin(nin)
        
        if PatientProfile.objects.filter(nin_hash=nin_hash).exists():
            return Response({"detail": "This NIN is already associated with another account."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not can_attempt_nin_verification(user):
            return Response({"detail": "You have reached the maximum number of attempts to verify your NIN today. Please contact our support team for assistance."}, status=status.HTTP_400_BAD_REQUEST)
        
        if nin_checked_before(user, nin_hash):
            return Response({"detail": "This NIN has already been checked and is invalid."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reference = verify_nin_request(nin)
        except Exception as e:
            NINVerificationAttempt.objects.create(user=user, nin_hash=nin_hash, success=False)
            return Response({"detail": str(e)}, status=400)
        
        NINVerificationAttempt.objects.create(user=user, nin_hash=nin_hash, success=True)

        patient_profile.nin_verified = True
        patient_profile.nin_hash = nin_hash
        patient_profile.save(update_fields=['nin_verified', 'nin_hash'])
        
        return self._generate_login_response(user)
    
    def _generate_login_response(self, user):
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        data = {"access": access, "refresh": str(refresh)}

        response = Response(data, status=200)

        set_refresh_cookie(response)
        response.data["data"]["role"] = user.role
        
        mailer.send(
                subject="New Login Alert",
                body = "There was a login attempt on your DOCUHEALTH account. If this was you, you can ignore this message. \n\nIf this was not you, please contact our support team at support@docuhealthservices.com \n\n\nFrom the Docuhealth Team",
                recipient=user.email,         
            )

        return response
    
@extend_schema(tags=["Auth"], summary="Send OTP to new user email")
class SendEmailOTPView(generics.GenericAPIView):
    serializer_class = UpdateEmailSerializer
    permission_classes = [IsAuthenticatedHospitalStaff | IsAuthenticatedHospitalAdmin | IsAuthenticatedPatient]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_email = serializer.validated_data['new_email']
        
        if User.objects.filter(email=new_email).exists():
            return Response({"detail": "This email is already in use."}, status=status.HTTP_400_BAD_REQUEST)
        
        EmailChange.change_email(user, new_email)
        
        if hasattr(user, 'hospital_staff_profile'):
            user_name = user.hospital_staff_profile.full_name
        elif hasattr(user, 'hospital_profile'):
            user_name = user.hospital_profile.name
        elif hasattr(user, 'patient_profile'):
            user_name = user.patient_profile.full_name
            
        otp = OTP.generate_otp(user)
        context = {"user_name": user_name, "otp": otp}
        html_content = render_to_string('emails/otp.html', context)
        
        mailer.send(
            subject="Verify your new email address",
            body=html_content,
            recipient=new_email,
            is_html=True
        )
        
        return Response({"detail": "OTP sent successfully"}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Auth"], summary="Verify OTP sent to new email")
class VerifyEmailOTPView(generics.GenericAPIView):
    serializer_class = VerifyEmailOTPSerializer
    permission_classes = [IsAuthenticatedHospitalStaff | IsAuthenticatedHospitalAdmin | IsAuthenticatedPatient]
    
    @transaction.atomic()
    def patch(self, request, *args, **kwargs):
        user = request.user
        otp_instance = user.otp
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email_change = user.email_change
        new_email = email_change.new_email
        otp = serializer.validated_data['otp']
        
        valid, message = otp_instance.verify(otp)
        if not valid:
            return Response({"detail": message, "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
        email_change.is_verified = True
        email_change.save(update_fields=['is_verified'])
        
        user.email = new_email
        user.save(update_fields=['email'])
        
        return Response({"detail": "Email updated successfully"}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Auth"], summary="Update user profile information")
class UpdateProfileView(generics.UpdateAPIView):
    serializer_class = UpdateProfileSerializer
    permission_classes = [IsAuthenticatedHospitalStaff | IsAuthenticatedPatient]
    http_method_names = ['patch']
    
    def get_object(self):
        user = self.request.user
        if hasattr(user, 'hospital_staff_profile'):
            return user.hospital_staff_profile
        elif hasattr(user, 'patient_profile'):
            return user.patient_profile
        else:
            raise NotFound("Profile not found for the user.")
        
@extend_schema(tags=["Auth"], summary="Update hospital admin profile information")
class UpdateHospitalAdminProfileView(generics.UpdateAPIView):
    serializer_class = UpdateHospitalAdminProfileSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin]
    http_method_names = ['patch']
    
    def get_object(self):
        user = self.request.user
        if hasattr(user, 'hospital_profile'):
            return user.hospital_profile
        else:
            raise NotFound("Profile not found for the user.")
        
@extend_schema(tags=["Patient"], summary="Patient sign up")
class CreatePatientView(generics.CreateAPIView, PublicGenericAPIView):
    serializer_class = CreatePatientSerializer
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        
        existing_inactive_user = User.objects.filter(email=email, is_active=False).first()
        if existing_inactive_user:
            existing_inactive_user.delete()  

        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = serializer.save()
        otp = OTP.generate_otp(user)
        
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
        
@extend_schema(tags=["Patient"])
class UpdatePatientView(generics.UpdateAPIView):
    serializer_class = UpdatePatientSerializer
    permission_classes = [IsAuthenticatedPatient]
    http_method_names = ['patch']
    
    def get_object(self):
        return self.request.user

@extend_schema(tags=["Patient"])
class PatientDashboardView(generics.GenericAPIView):
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticatedPatient]

    def get(self, request, *args, **kwargs):
        user = request.user
        profile = user.patient_profile 

        queryset = MedicalRecord.objects.filter(patient=profile).select_related("patient", "subaccount", "hospital").prefetch_related("drug_records", "attachments").order_by("-created_at")
        page = self.paginate_queryset(queryset)
        records_serializer = self.get_serializer(page, many=True)
        
        paginated_data = self.get_paginated_response(records_serializer.data).data
        
        is_subscribed = Subscription.objects.filter(user=user, status=Subscription.SubscriptionStatus.ACTIVE).exists()

        return Response({
            "patient_info": {
                "firstname": profile.firstname,
                "lastname": profile.lastname,
                "middlename": profile.middlename,
                "hin": profile.hin,
                "dob": profile.dob,
                "id_card_generated": profile.id_card_generated,
                "email": user.email,
                "phone_num": profile.phone_num,
                "emergency": profile.emergency,
                "is_subscribed": is_subscribed
            },
            **paginated_data
        })
    
@extend_schema(tags=["Patient"])   
class ListCreateSubaccountView(generics.ListCreateAPIView):
    serializer_class = CreateSubaccountSerializer
    permission_classes = [IsAuthenticatedPatient]
    
    def get_queryset(self):
        return SubaccountProfile.objects.filter(parent=self.request.user.patient_profile).select_related("parent").order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(parent=self.request.user.patient_profile)

@extend_schema(tags=["Patient"])
class UpgradeSubaccountView(generics.CreateAPIView):
    serializer_class = UpgradeSubaccountSerializer
    permission_classes = [IsAuthenticatedPatient]
    
    def perform_create(self, serializer):
        verify_url = serializer.validated_data.pop("verify_url")
        user = serializer.save()
        otp = OTP.generate_otp(user)
        
        mailer.send(
            subject="Verify your email",
            body=(
                f"Enter the OTP below into the required field \n"
                f"The OTP will expire in 10 mins\n\n"
                f"OTP: {otp}\n\n"
                
                f"Please use the link below and enter your OTP: \n\n"
                f"{verify_url}\n\n"
                
                f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
                f"From the Docuhealth Team"
            ),
            recipient=user.email,
        )
        
@extend_schema(tags=["Patient"])
class DeletePatientAccountView(generics.DestroyAPIView):
    serializer_class = UpdatePatientSerializer
    permission_classes = [IsAuthenticatedPatient]
    
    def get_object(self):
        return self.request.user
    
    def perform_destroy(self, instance):
        profile = instance.patient_profile
        profile.soft_delete()
        
@extend_schema(tags=['Patient'])
class GeneratePatientIdCard(generics.UpdateAPIView):
    serializer_class = GeneratePatientIDCardSerializer
    permission_classes = [IsAuthenticatedPatient]
    http_method_names = ['patch']
    
    def get_object(self):
        return self.request.user.patient_profile

    def perform_update(self, serializer):
        patient = self.get_object()
        patient.generate_id_card()
        
@extend_schema(tags=['Patient'])
class GenerateSubaccountIdCard(generics.UpdateAPIView):
    queryset = SubaccountProfile.objects.all()
    serializer_class = GenerateSubaccountIDCardSerializer
    permission_classes = [IsAuthenticatedPatient]
    http_method_names = ['patch']
    lookup_field = 'hin'
    
    def perform_update(self, serializer):
        subaccount = self.get_object()
        subaccount.generate_id_card()
        
@extend_schema(tags=['Patient'])
class ToggleEmergencyView(generics.UpdateAPIView):
    serializer_class = PatientEmergencySerializer
    permission_classes = [IsAuthenticatedPatient]
    http_method_names = ['patch']
    
    def get_object(self):
        return self.request.user.patient_profile

    def perform_update(self, serializer):
        patient = self.get_object()
        patient.toggle_emergency()
        
@extend_schema(tags=["Hospital Admin"])  
class TeamMemberCreateView(generics.CreateAPIView):
    serializer_class = TeamMemberCreateSerializer
    permission_classes = [IsAuthenticatedHospitalAdmin]
    
    @transaction.atomic
    def perform_create(self, serializer):
        hospital = self.request.user.hospital_profile
        invitation_message = serializer.validated_data.pop("invitation_message")
        login_url = serializer.validated_data.pop("login_url")
        user = serializer.save(is_active=True)
        
        mailer.send(
                subject=f"Welcome to {hospital.name} hospital",
                body=(
                    f"{invitation_message} \n\n"
                    
                    f"Please use the link below to log in to your account: \n\n"
                    f"{login_url}\n\n"
                    
                    f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
                    f"From the Docuhealth Team"
                ),
                recipient=user.email,
            )
        
@extend_schema(tags=["Hospital Admin", "Receptionist", "Nurse", "Doctor"])
class TeamMemberListView(generics.ListAPIView):
    serializer_class = HospitalStaffInfoSerilizer
    permission_classes = [IsAuthenticatedHospitalAdmin | IsAuthenticatedHospitalStaff]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == User.Role.HOSPITAL:
            hospital = user.hospital_profile
        else:
            hospital = user.hospital_staff_profile.hospital
            
        return HospitalStaffProfile.objects.filter(hospital=hospital).select_related("hospital").order_by('-created_at')
        
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
    
@extend_schema(tags=["Doctor"], summary='Doctor Dashboard')
class DoctorDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedDoctor]
    serializer_class = HospitalStaffInfoSerilizer

    def get(self, request, *args, **kwargs):
        user = request.user
        staff = user.hospital_staff_profile
        hospital = staff.hospital
        hospital_user = hospital.user
        
        doctor_info = self.get_serializer(staff).data
        hospital_theme = {
            "bg_image": hospital.bg_image.url,
            "theme_color": hospital.theme_color
        }
        
        is_subscribed = Subscription.objects.filter(user=hospital_user, status=Subscription.SubscriptionStatus.ACTIVE).exists()
        
        doctor_info["is_subscribed"] = is_subscribed
        
        return Response({
            "doctor": doctor_info,
            "theme": hospital_theme
        }, status=status.HTTP_200_OK)
        
@extend_schema(tags=["Nurse"], summary='Nurse Dashboard')
class NurseDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedNurse]

    def get(self, request, *args, **kwargs):
        user = request.user
        staff = user.hospital_staff_profile
        hospital = staff.hospital
        hospital_user = hospital.user
        ward = staff.ward
        
        hospital_theme = {
            "bg_image": hospital.bg_image.url,
            "theme_color": hospital.theme_color
        }

        response = {}
        is_subscribed = Subscription.objects.filter(user=hospital_user, status=Subscription.SubscriptionStatus.ACTIVE).exists()
        
        nurse_info = HospitalStaffInfoSerilizer(staff).data
        nurse_info["is_subscribed"] = is_subscribed
        
        response['theme'] = hospital_theme
        response['nurse'] = nurse_info
        
        if ward:
            ward_info = WardBasicInfoSerializer(ward).data
            response['ward_info'] = ward_info

        return Response(response, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Receptionist"], summary='Receptionist Dashboard')
class ReceptionistDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedReceptionist]

    def get(self, request, *args, **kwargs):
        user = request.user
        staff = user.hospital_staff_profile
        hospital = staff.hospital
        hospital_user = hospital.user
        
        is_subscribed = Subscription.objects.filter(user=hospital_user, status=Subscription.SubscriptionStatus.ACTIVE).exists()
        hospital_theme = {
            "bg_image": hospital.bg_image.url,
            "theme_color": hospital.theme_color
        }
        
        receptionist_info = HospitalStaffInfoSerilizer(staff).data
        receptionist_info["is_subscribed"] = is_subscribed
        
        return Response({
            "receptionist": receptionist_info,
            "theme": hospital_theme
        }, status=status.HTTP_200_OK)
        
@extend_schema(tags=["Receptionist"], summary="Create a new patient account")
class ReceptionistCreatePatientView(generics.CreateAPIView):
    serializer_class = ReceptionistCreatePatientSerializer
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
        verify_url = serializer.validated_data.pop("verify_url")
        user = serializer.save()
        otp = OTP.generate_otp(user, expiry_minutes=60)
        
        mailer.send(
            subject="Verify your email",
            body=(
                f"Enter the OTP below into the required field \n"
                f"The OTP will expire in 10 mins\n\n"
                f"OTP: {otp}\n\n"

                f"Please use the link below and enter your OTP: \n\n"
                f"{verify_url}\n\n"
                    
                f"If you did not initiate this request, please contact support@docuhealthservices.com\n\n"
                f"From the Docuhealth Team"
            ),
            recipient=user.email,
        )
        
        HospitalPatientActivity.objects.create(patient=user.patient_profile, staff=staff, hospital=hospital, action="create_patient_account")
        
@extend_schema(tags=["Receptionist"], summary="Get patient details by HIN")
class GetPatientDetailsView(generics.RetrieveAPIView):
    serializer_class = PatientFullInfoSerializer
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
        
        serializer = self.get_serializer(patient_user.patient_profile)
        
        HospitalPatientActivity.objects.create(patient=patient_user.patient_profile, staff=staff, hospital=hospital, action="check_patient_info")
        
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(tags=["Receptionist", "Nurse", "Doctor"], summary="Get hospital staff by role")
class GetStaffByRoleView(generics.ListAPIView):
    permission_classes = [IsAuthenticatedHospitalStaff | IsAuthenticatedHospitalAdmin]
    serializer_class = HospitalStaffInfoSerilizer
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
    
