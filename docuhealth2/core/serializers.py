from rest_framework import serializers
from .models import User
from patients.models import PatientProfile
from patients.serializers import PatientProfileSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, write_only=True, min_length=6, max_length=6)

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
    profile = PatientProfileSerializer(required=True)
    
    class Meta:
        model = User
        fields = ['email', 'role', 'hin', 'street', 'city', 'state','country', 'created_at', 'updated_at', 'profile', 'password' ]
        
        read_only_fields = ['id', 'hin', 'created_at', 'updated_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        profile_data = validated_data.pop('profile')
        role = validated_data.get('role')
        
        house_no = validated_data.pop('house_no')
        if house_no:
            validated_data['street'] = f'{house_no}, {validated_data['street']}'

        user = User.objects.create_user(email=email, password=password, **validated_data)

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
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
