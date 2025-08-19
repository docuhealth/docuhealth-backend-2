from rest_framework import serializers
from .models import User
from ..patients.models import PatientProfile
from ..patients.serializers import PatientProfileSerializer

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    profile = PatientProfileSerializer(required=True)
    # role = serializers.ChoiceField(choices=[choice[0] for choice in User.Role.choices])
    
    house_no = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'role', 'hin',
            'notification_settings',
            'street', 'city', 'state', 'country',
            'created_at', 'updated_at',
            'profile',
        ]
        read_only_fields = ['id', 'hin', 'created_at', 'updated_at']


    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role')
        profile_data = validated_data.pop('profile')

        user = User.objects.create_user(password=password, **validated_data)

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
