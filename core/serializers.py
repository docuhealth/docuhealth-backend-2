from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from .models import User, OTP
from patients.models import PatientProfile
from patients.serializers import PatientProfileSerializer

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

        token["hin"] = user.hin
        token["role"] = user.role
        token["email"] = user.email

        return token

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    profile = PatientProfileSerializer(required=True)
    
    class Meta:
        model = User
        fields = ['email', 'role', 'hin', 'street', 'city', 'state','country', 'created_at', 'updated_at', 'profile', 'password', 'house_no' ]
        
        read_only_fields = ['id', 'hin', 'created_at', 'updated_at']

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        role = validated_data.get('role')
        
        house_no = validated_data.pop('house_no', None)
        if house_no:
            validated_data['street'] = f'{house_no}, {validated_data['street']}'

        user = super().create(validated_data)

        if role == User.Role.PATIENT:
            PatientProfile.objects.create(user=user, **profile_data)

        return user

    def update(self, instance, validated_data):
        """
        Update User and optionally nested PatientProfile
        """
        profile_data = validated_data.pop('profile', None)
        password = validated_data.pop('password', None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update password if provided
        if password:
            instance.set_password(password)

        instance.save()

        # Update nested profile if provided
        if profile_data:
            profile = getattr(instance, 'patientprofile', None)
            if profile:
                for attr, value in profile_data.items():
                    setattr(profile, attr, value)
                profile.save()
            else:
                # If somehow no profile exists, create it
                PatientProfile.objects.create(user=instance, **profile_data)

        return instance


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    