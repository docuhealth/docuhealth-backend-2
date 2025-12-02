from rest_framework import serializers

from hospitals.models import HospitalStaffProfile, HospitalWard
from core.models import User
from core.serializers import BaseUserCreateSerializer

class CreateStaffProfieSerializer(serializers.ModelSerializer):
    ward = serializers.PrimaryKeyRelatedField(write_only=True, queryset=HospitalWard.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = HospitalStaffProfile
        fields = ['firstname', 'lastname', 'phone_no', 'role', 'specialization', 'ward', 'gender']
        
    def get_fields(self):
        fields = super().get_fields()
        
        from .services import WardNameSerializer 
        fields["ward_info"] = WardNameSerializer(source="ward", read_only=True)
        
        return fields

class HospitalStaffInfoSerilizer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")
    
    class Meta:
        model = HospitalStaffProfile
        fields = ["firstname", "lastname", "phone_no", "role", "staff_id", "email", "ward", "gender"]
        
    def get_fields(self):
        fields = super().get_fields()
        
        from .services import WardNameSerializer 
        fields["ward_info"] = WardNameSerializer(source="ward", read_only=True)
        
        return fields

class TeamMemberCreateSerializer(BaseUserCreateSerializer):
    profile = CreateStaffProfieSerializer(required=True, source="hospital_staff_profile")
    invitation_message = serializers.CharField(write_only=True, required=True)
    login_url = serializers.URLField(required=True, write_only=True)
    
    class Meta(BaseUserCreateSerializer.Meta):
        fields = BaseUserCreateSerializer.Meta.fields + ['profile', 'invitation_message']
        
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