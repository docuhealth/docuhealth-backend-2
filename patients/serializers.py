from rest_framework import serializers

from .models import PatientProfile, Subaccount
from core.models import User

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['dob', 'gender', 'phone_num', 'firstname', 'lastname', 'middlename', 'referred_by']
        
class SubaccountSerializer(serializers.ModelSerializer):
    # parent = serializers.SlugRelatedField(slug_field="hin", queryset=User.objects.all(), required=True)
    
    class Meta:
        model = Subaccount
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'parent')