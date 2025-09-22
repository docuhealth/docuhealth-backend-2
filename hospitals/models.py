from django.db import models
from core.models import User

from docuhealth2.models import BaseModel
from docuhealth2.utils.generate import generate_HIN

class HospitalProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hospital_profile")
    hin = models.CharField(max_length=20, unique=True)
    
    firstname = models.CharField(max_length=100, blank=True)
    lastname = models.CharField(max_length=100, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.hin:  
            while True:
                new_hin = generate_HIN()
                if not HospitalProfile.all_objects.filter(hin=new_hin).exists():
                    self.hin = new_hin
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"HospitalAdmin: {self.firstname} {self.lastname} ({self.user.email})"


class DoctorProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="doctors")
    doc_id = models.CharField(max_length=20, unique=True)
    
    specialization = models.CharField(max_length=100, blank=True)
    license_no = models.CharField(max_length=50, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.doc_id:  
            while True:
                new_doc_id = generate_HIN()
                if not DoctorProfile.all_objects.filter(doc_id=new_doc_id).exists():
                    self.doc_id = new_doc_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Doctor: {self.user.email} ({self.specialization})"
