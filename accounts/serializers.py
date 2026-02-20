from django.core.exceptions import ValidationError
from django.utils import timezone

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from docuhealth2.mixins import StrictFieldsMixin

from .models import EmailChange, User, OTP, UserProfileImage, PatientProfile, SubaccountProfile, HospitalStaffProfile

from facility.models import HospitalWard
from facility.serializers import WardNameSerializer

from organizations.models import HospitalProfile, Subscription

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get("email")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email"})
        
        self.user = user
        self.email = email
        
        return validated_data
    
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, write_only=True, min_length=6, max_length=6)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get("email")
        otp = validated_data.get("otp")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email"})
        
        try:
            otp_instance = user.otp
        except OTP.DoesNotExist:
           raise serializers.ValidationError({"otp": "No OTP found"})

        self.user = user
        self.otp_instance = otp_instance
        self.otp = otp
        
        return validated_data

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        return token

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)

class BaseUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=True)

    class Meta:
        model = User
        fields = ["email", "password"]
        read_only_fields = ["id", "created_at", "updated_at"]

class UserProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfileImage
        fields = ['id', 'image']
        
class UpdatePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True, min_length=8)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        old_password = validated_data['old_password']
        user = self.context['request'].user
        
        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})
        
        return validated_data
    
class UpdateEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(write_only=True, required=True)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        new_email = validated_data['new_email']
        if User.objects.filter(email=new_email).exclude(pk=self.context['request'].user.pk).exists():
            raise serializers.ValidationError({"new_email": "A user with this email already exists."})
        
        return validated_data
    
class VerifyEmailOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(required=True, write_only=True, min_length=6, max_length=6)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        user = self.context['request'].user
        
        if not EmailChange.objects.filter(user=user, is_verified=False).exists():
            raise serializers.ValidationError({"new_email": "No email change request found for this account."})
        
        return validated_data
    
class UpdateProfileSerializer(StrictFieldsMixin, serializers.Serializer):
    firstname = serializers.CharField(required=False, allow_blank=True)
    lastname = serializers.CharField(required=False, allow_blank=True)
    phone_num = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
    
class UpdateHospitalAdminProfileSerializer(StrictFieldsMixin, serializers.ModelSerializer):
        profile_image = serializers.DictField(required=False, allow_null=True, read_only=True)
        bg_image = serializers.DictField(required=False, allow_null=True, read_only=True)
        
        class Meta:
            model = HospitalProfile
            fields = ['name', 'bg_image', "theme_color", "profile_image"]
    
class PatientFullInfoSerializer(serializers.ModelSerializer):
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    email = serializers.EmailField(read_only=True, source="user.email")
    
    class Meta:
        model = PatientProfile
        fields = ['dob', 'gender', 'phone_num', 'firstname', 'lastname', 'middlename', 'referred_by', 'hin', 'street', 'city', 'state', 'country', 'house_no', 'email']
        read_only_fields = ['hin']
        
class CreatePatientSerializer(BaseUserCreateSerializer):
    profile = PatientFullInfoSerializer(required=True, source="patient_profile")
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ["profile"]

    def create(self, validated_data):
        profile_data = validated_data.pop("patient_profile")
        validated_data['role'] = User.Role.PATIENT
        
        house_no = profile_data.pop("house_no", None)
        if house_no:
            profile_data["street"] = f'{house_no}, {profile_data["street"]}'
        
        user = super().create(validated_data)
        PatientProfile.objects.create(user=user, **profile_data)
        
        return user
    
class ReceptionistCreatePatientSerializer(BaseUserCreateSerializer):
    profile = PatientFullInfoSerializer(required=True, source="patient_profile")
    verify_url = serializers.URLField(write_only=True, required=True)
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ["profile", "verify_url"]

    def create(self, validated_data):
        profile_data = validated_data.pop("patient_profile")
        validated_data['role'] = User.Role.PATIENT
        
        house_no = profile_data.pop("house_no", None)
        if house_no:
            profile_data["street"] = f'{house_no}, {profile_data["street"]}'
        
        user = super().create(validated_data)
        PatientProfile.objects.create(user=user, **profile_data)
        
        return user
    
class UpdatePatientProfileSerializer(StrictFieldsMixin , serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        exclude = ['is_deleted', 'deleted_at', 'created_at', 'user', 'hin', 'id_card_generated', 'referred_by', 'emergency']
        
class UpdatePatientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, write_only=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)
    profile = UpdatePatientProfileSerializer(required=False)  
    
    class Meta:
        model = User
        fields = ['email', 'password', 'profile', 'updated_at']  
        read_only_fields = ['updated_at']
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get('email', None)
        
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("A user with this email already exists.")
        
        profile_data = validated_data.get('profile')
        if profile_data:
            profile_serializer = PatientFullInfoSerializer(
                instance=self.instance.patient_profile,
                data=profile_data,
                partial=True  
            )
            profile_serializer.is_valid(raise_exception=True)
            validated_data['profile'] = profile_serializer.validated_data

        return validated_data
        
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        if 'email' in validated_data:
            instance.email = validated_data['email']

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
            
        instance.updated_at = timezone.now()
        
        fields = []
        if profile_data:
            profile = instance.patient_profile
            for attr, value in profile_data.items():
                if value is not None:
                    fields.append(attr)
                    setattr(profile, attr, value)
            profile.save(update_fields=fields)

        instance.save()
        return instance
    
class PatientEmergencySerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['hin', 'emergency']
        read_only_fields = ['hin']

class CreateSubaccountSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = SubaccountProfile
        exclude = ['is_deleted', 'deleted_at', 'created_at', 'updated_at', 'id_card_generated', 'parent']
        read_only_fields = ['hin' ]
    
    def create(self, validated_data):
        user = User.objects.create(role="subaccount")
        validated_data['user'] = user
            
        return super().create(validated_data)
        
class UpgradeSubaccountSerializer(serializers.ModelSerializer):
    subaccount = serializers.SlugRelatedField(slug_field="hin", queryset=SubaccountProfile.objects.all(), write_only=True)
    
    phone_num = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    verify_url = serializers.URLField(write_only=True, required=True)
    
    state = serializers.CharField(write_only=True, required=False, allow_blank=True)
    country = serializers.CharField(write_only=True, required=False, allow_blank=True)
    street = serializers.CharField(write_only=True, required=False, allow_blank=True)
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    city = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'phone_num', 'subaccount', 'verify_url', 'street', 'city', 'state', 'country', 'house_no']
        read_only_fields = ('id', 'created_at', 'updated_at')
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        email = validated_data.get('email')
        
        existing_user = User.objects.filter(email=email).exists()
        if existing_user:
            raise ValidationError("A user with this email already exists.")
        
        return validated_data
        
    def create(self, validated_data):
        subaccount_profile = validated_data.pop('subaccount')
        
        phone_num = validated_data.pop('phone_num')
        password = validated_data.pop('password')
        
        house_no = validated_data.pop("house_no", None)
        if house_no:
            validated_data["street"] = f'{house_no}, {validated_data["street"]}'
        
        subaccount_user = subaccount_profile.user
        validated_data['role'] = User.Role.PATIENT
        
        patient_profile_data = {
            "firstname": subaccount_profile.firstname, 
            "lastname": subaccount_profile.lastname,
            "middlename": subaccount_profile.middlename,
            "dob": subaccount_profile.dob,
            "gender": subaccount_profile.gender,
            "phone_num": phone_num,
            
            "id_card_generated": subaccount_profile.id_card_generated
        }
        
        subaccount_user.set_password(password)
        for field, value in validated_data.items():
            setattr(subaccount_user, field, value)
            
        subaccount_user.save()
        
        PatientProfile.objects.create(user=subaccount_user, **patient_profile_data)
        
        return subaccount_user
    
class GeneratePatientIDCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['hin', 'id_card_generated']
        read_only_fields = ['hin']
        
class GenerateSubaccountIDCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubaccountProfile
        fields = ['hin', 'id_card_generated']
        read_only_fields = ['hin']
        
class PatientBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['hin', 'firstname', 'lastname', 'gender', 'dob']
        
class VerifyUserNINSerializer(serializers.Serializer):
    patient = serializers.SlugRelatedField(slug_field="hin", queryset=PatientProfile.objects.all(), write_only=True)
    nin = serializers.CharField(write_only=True, required=True, min_length=11, max_length=11)
    
class CreateStaffProfileSerializer(serializers.ModelSerializer):
    ward = serializers.PrimaryKeyRelatedField(write_only=True, queryset=HospitalWard.objects.all(), required=False, allow_null=True)
    ward_info = WardNameSerializer(read_only=True, source="ward")
    
    class Meta:
        model = HospitalStaffProfile
        fields = ['firstname', 'lastname', 'phone_num', 'role', 'specialization', 'ward', 'gender', "ward_info"]
        
    # def get_fields(self):
    #     fields = super().get_fields()
        
    #     from .services import WardNameSerializer 
    #     fields["ward_info"] = WardNameSerializer(source="ward", read_only=True)
        
    #     return fields

class HospitalStaffInfoSerilizer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")
    ward_info = WardNameSerializer(read_only=True, source="ward")
    
    class Meta:
        model = HospitalStaffProfile
        fields = ["firstname", "lastname", "phone_num", "role", "staff_id", "email", "ward", "gender", "ward_info"]
        
class TeamMemberCreateSerializer(BaseUserCreateSerializer):
    profile = CreateStaffProfileSerializer(required=True, source="hospital_staff_profile")
    invitation_message = serializers.CharField(write_only=True, required=True)
    login_url = serializers.URLField(required=True, write_only=True)
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ['profile', 'invitation_message', 'login_url']
        
    def create(self, validated_data):
        profile_data = validated_data.pop("hospital_staff_profile")
        validated_data['role'] = User.Role.HOSPITAL_STAFF
        
        hospital = self.context['request'].user.hospital_profile
        
        user = super().create(validated_data)
        HospitalStaffProfile.objects.create(user=user, hospital=hospital, **profile_data)
        
        return user
    
class RemoveTeamMembersSerializer(serializers.Serializer):
    staff_ids = serializers.ListField(child=serializers.CharField(), allow_empty=False, required=True)
    
class TeamMemberUpdateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalStaffProfile
        fields = ['role']
        
    def update(self, instance, validated_data):
        new_role = validated_data['role']

        if instance.role == new_role:
            raise serializers.ValidationError({"role": "Role already assigned"})
        
        instance.role = new_role
        instance.save(update_fields=["role"])
        
        return instance
    
class HospitalStaffBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalStaffProfile
        fields = ['staff_id', 'firstname', 'lastname', 'role', 'specialization']
        
class PatientDashboardInfoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            "firstname", "lastname", "middlename", "hin", "dob", 
            "id_card_generated", "email", "phone_num", "emergency", "is_subscribed"
        ]

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            user=obj.user, 
            status=Subscription.SubscriptionStatus.ACTIVE
        ).exists()