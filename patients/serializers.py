from rest_framework import serializers

from .models import PatientProfile, Subaccount
from core.models import User
from docuhealth2.utils.generate import generate_HIN

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['dob', 'gender', 'phone_num', 'firstname', 'lastname', 'middlename', 'referred_by']
        
class SubaccountSerializer(serializers.ModelSerializer):
    # parent = serializers.SlugRelatedField(slug_field="hin", queryset=User.objects.all(), required=True)
    
    def create(self, validated_data):
        while True:
            hin = generate_HIN()
            if not Subaccount.objects.filter(hin=hin).exists():
                validated_data["hin"] = hin
                break
            
        return super().create(validated_data)
    
    class Meta:
        model = Subaccount
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'parent', 'hin')