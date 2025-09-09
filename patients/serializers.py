from rest_framework import serializers

from .models import PatientProfile, Subaccount
from core.models import User
from docuhealth2.utils.generate import generate_HIN

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['dob', 'gender', 'phone_num', 'firstname', 'lastname', 'middlename', 'referred_by']
        
class CreateSubaccountSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Subaccount
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'parent', 'hin']
    
    def create(self, validated_data):
        parent = self.context['request'].user
        user = User.objects.create(role="subaccount")
        
        validated_data['parent'] = parent
        validated_data['user'] = user
            
        return super().create(validated_data)
        
class UpgradeSubaccountSerializer(serializers.ModelSerializer):
    subaccount = serializers.SlugRelatedField(slug_field="hin", queryset=User.objects.all(), write_only=True)
    
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
        fields = ['email', 'street', 'city', 'state', 'country', 'password', 'house_no', 'phone_num', 'subaccount']
        read_only_fields = ('id', 'created_at', 'updated_at')
        
    def create(self, validated_data):
        house_no = validated_data.pop('house_no', None)
        if house_no:
            validated_data['street'] = f'{house_no}, {validated_data['street']}'
            
        subaccount_user = validated_data.pop('subaccount')
        phone_num = validated_data.pop('phone_num')
        password = validated_data.pop('password')
        
        subaccount_profile = subaccount_user.subaccount_profile
        validated_data['role'] = 'patient'
        
        patient_profile_data = {
            "firstname": subaccount_profile.firstname, 
            "lastname": subaccount_profile.lastname,
            "middlename": subaccount_profile.middlename,
            "dob": subaccount_profile.dob,
            "gender": subaccount_profile.gender,
            "phone_num": phone_num
        }
        
        subaccount_user.set_password(password)
        for field, value in validated_data.items():
            setattr(subaccount_user, field, value)
            
        subaccount_user.save()
        
        PatientProfile.objects.create(user=subaccount_user, **patient_profile_data)
        
        return subaccount_user
            