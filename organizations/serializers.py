from django.core.exceptions import ValidationError
from rest_framework import serializers

from accounts.models import User
from accounts.serializers import BaseUserCreateSerializer

from .models import HospitalProfile, HospitalInquiry, HospitalVerificationRequest, VerificationToken, SubscriptionPlan, Subscription, PharmacyPartner, PharmacyProfile

from .requests import create_plan

class HospitalProfileSerializer(serializers.ModelSerializer):
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    class Meta:
        model= HospitalProfile
        fields = ['name', 'hin', 'street', 'city', 'state', 'country', 'house_no']
        read_only_fields = ['hin']
        
class CreateHospitalSerializer(BaseUserCreateSerializer):
    profile = HospitalProfileSerializer(required=True, source="hospital_profile")
    
    verification_token = serializers.CharField(write_only=True, required=True, allow_blank=True, max_length=255)
    verification_request = serializers.PrimaryKeyRelatedField(write_only=True, queryset=HospitalVerificationRequest.objects.all(), required=True)
    
    login_url = serializers.URLField(required=True, write_only=True)
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ["profile", "verification_token", "verification_request", "login_url"]
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        verification_request = validated_data.pop("verification_request")
        token = validated_data.pop("verification_token")
        
        if verification_request.status != HospitalVerificationRequest.Status.APPROVED:
            raise ValidationError({"verification_request": "This request is not approved yet"})
        
        try:
            token_instance = verification_request.verification_token
        except VerificationToken.DoesNotExist:
            raise ValidationError({"verification_token": "Verification token not found"})
        
        valid, message = token_instance.verify(token)
        if not valid:
            raise ValidationError({"verification_token": message})
        
        return validated_data

    def create(self, validated_data):
        profile_data = validated_data.pop("hospital_profile")
        validated_data['role'] = User.Role.HOSPITAL
        
        house_no = profile_data.pop("house_no", None)
        if house_no:
            profile_data["street"] = f'{house_no}, {profile_data["street"]}'
        
        user = super().create(validated_data)
        HospitalProfile.objects.create(user=user, **profile_data)
        
        return user
    
class HospitalInquirySerializer(serializers.ModelSerializer):
    redirect_url = serializers.URLField(required=True, allow_blank=True, write_only=True)
    
    class Meta:
        model= HospitalInquiry
        exclude = ['is_deleted', 'deleted_at']
        read_only_fields = ['status', 'created_at', 'updated_at']
        
class HospitalVerificationRequestSerializer(serializers.ModelSerializer):
    inquiry = serializers.PrimaryKeyRelatedField(queryset=HospitalInquiry.objects.all())
    documents = serializers.ListField(child=serializers.DictField())
    
    class Meta:
        model= HospitalVerificationRequest
        exclude = ['is_deleted', 'deleted_at' ]
        read_only_fields = ['status', 'created_at', 'updated_at', 'reviewed_by']
        
class ApproveVerificationRequestSerializer(serializers.Serializer):
    verification_request = serializers.PrimaryKeyRelatedField(queryset=HospitalVerificationRequest.objects.all())
    redirect_url = serializers.URLField(required=True, write_only=True)
    
class HospitalFullInfoSerializer(serializers.ModelSerializer):
    hospital_profile = HospitalProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "hospital_profile"]
        
class HospitalBasicInfoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")
    
    class Meta:
        model = HospitalProfile
        fields = ['hin', 'name', 'email']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    features = serializers.ListField(child=serializers.CharField())
    
    class Meta:
        model = SubscriptionPlan
        exclude = ["deleted_at", "is_deleted", ]
        read_only_fields = ["paystack_plan_code", "created_at", "updated_at", ]
        
    def create(self, validated_data):
        payload = {
            "name": validated_data["name"],
            "interval": validated_data["interval"],
            "amount": int(validated_data["price"] * 100),
            "description": validated_data["description"],
            "currency": "NGN",
            }
        
        paystack_plan_code = create_plan(payload)
        validated_data["paystack_plan_code"] = paystack_plan_code
        
        return super().create(validated_data) # TODO: Move to view
    
class SubscriptionSerializer(serializers.ModelSerializer):
    plan = serializers.SlugRelatedField(slug_field="paystack_plan_code", queryset=SubscriptionPlan.objects.all())
    
    class Meta:
        model = Subscription
        exclude = ["deleted_at", "is_deleted"]
        read_only_fields = ["user", "paystack_subscription_code", "status", "will_renew", "start_date", "end_date", "next_payment_date", "last_payment_date", "authorization_code", "created_at", "updated_at"]
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        plan = validated_data.get("plan")
        user = self.context.get("user")
        print(user)
        
        if plan.role != user.role:
            raise serializers.ValidationError("This plan is not available for your role.")
        
        # if not plan.is_active:
        #     raise serializers.ValidationError("Current plan is not active")
        
        return validated_data
        
    def create(self, validated_data):
       user = self.context.get("user")
       plan = validated_data.get("plan")
       
       subscription, _ = Subscription.objects.update_or_create(user=user, defaults={"plan":plan})

       return subscription
   
class PharmacyProfileSerializer(serializers.ModelSerializer):
    building_no = serializers.CharField(required=False)
    documents = serializers.ListField(child=serializers.DictField())
    
    class Meta:
        model = PharmacyProfile   
        fields = ['name', 'license_no', 'documents', 'phone', 'message', 'building_no', 'street', 'city', 'state', 'country']
   
class PharmacyOnboardingRequestSerializer(BaseUserCreateSerializer):
    profile = PharmacyProfileSerializer(required=True, source="pharmacy_profile")
    
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = BaseUserCreateSerializer.Meta.fields + ["profile"]
        
class ListPharmacyOnboardingRequestSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")
    class Meta:
        model = PharmacyProfile
        fields = ["id", "pharm_code", "name", "license_no", "phone", "email", "status", "documents", "street", "city", "state", "country",  "created_at"]
        
class ApprovePharmacyOnboardingRequestSerializer(serializers.Serializer):
    pharmacy_id = serializers.PrimaryKeyRelatedField(queryset=PharmacyProfile.objects.filter(status=PharmacyProfile.Status.PENDING).select_related("user", "partner"))
    login_url = serializers.URLField(write_only=True, required=True)
    
class PharmacyRotateKeySerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    
class PharmacyPartnerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PharmacyPartner
        fields = ["name", "address", "phone"]
        read_only_fields = ["id", "created_at"]
    
class CreatePharmacyPartnerSerializer(BaseUserCreateSerializer):
    profile = PharmacyPartnerSerializer(required=True, source="pharmacy_partner")
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ["profile"]
        
    def create(self, validated_data):
        profile_data = validated_data.pop("pharmacy_partner")
        validated_data['role'] = User.Role.PHARMACY_PARTNER
        
        user = super().create(validated_data)
        PharmacyPartner.objects.create(user=user, **profile_data)
        
        return user
    
class RotatePharmacyCodeSerializer(serializers.Serializer):
    old_code = serializers.SlugRelatedField(slug_field="pharm_code", queryset=PharmacyProfile.objects.all().select_related("partner"), write_only=True, required=True)
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        request = self.context.get('request')
        partner = request.user.pharmacy_partner  
        pharmacy = validated_data.get('old_code')

        if pharmacy.partner != partner:
            raise serializers.ValidationError({
                "pharm_code": "This pharmacy is not registered under your partner account."
            })
            
        return validated_data
