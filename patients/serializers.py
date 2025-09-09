from rest_framework import serializers

from .models import PatientProfile, Subaccount
from core.models import User
from docuhealth2.utils.generate import generate_HIN

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['dob', 'gender', 'phone_num', 'firstname', 'lastname', 'middlename', 'referred_by']
        
class SubaccountSerializer(serializers.ModelSerializer):
    
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
        
class UpgradeSubaccountSerializer(serializers.ModelSerializer):
    subaccount = serializers.SlugRelatedField(slug_field="hin", queryset=Subaccount.objects.all())
    
    email = serializers.EmailField(required=True)
    phone_num = serializers.CharField(required=False)
    
    street = serializers.CharField(max_length=120, required=True)
    city = serializers.CharField(max_length=20, required=True)
    state = serializers.CharField(max_length=20, required=True)
    country = serializers.CharField(max_length=20, required=True)
    
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    house_no = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10)
    
    class Meta:
        model = User
        fields = ['email', 'hin', 'street', 'city', 'state','country', 'created_at', 'updated_at', 'profile', 'password', 'house_no']
        read_only_fields = ('id', 'created_at', 'updated_at', 'hin')
        
    def create(self, validated_data):
        validated_data['role'] = 'patient'
        
        house_no = validated_data.pop('house_no', None)
        if house_no:
            validated_data['street'] = f'{house_no}, {validated_data['street']}'

        user = super().create(validated_data) 
        PatientProfile.objects.create(user=user, )
            
        return user