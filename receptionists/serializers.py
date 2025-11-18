from rest_framework import serializers

from hospitals.models import HospitalStaffProfile

class ReceptionistInfoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = HospitalStaffProfile
        fields = ["firstname", "lastname", "phone_no", "role", "staff_id", "email"]
