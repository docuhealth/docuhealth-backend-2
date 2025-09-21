from django.db import models
from core.models import User

class HospitalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hospitaladmin_profile")
    hospital = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hospital_admins")
    
    firstname = models.CharField(max_length=100, blank=True)
    lastname = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"HospitalAdmin: {self.firstname} {self.lastname} ({self.user.email})"


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="doctors")
    
    specialization = models.CharField(max_length=100, blank=True)
    license_no = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Doctor: {self.user.email} ({self.specialization})"
