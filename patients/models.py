from django.db import models
from core.models import User

from docuhealth2.models import BaseModel
from docuhealth2.utils.generate import generate_HIN

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
    ('unknown', 'Unknown'),
]

class PatientProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    hin = models.CharField(max_length=20, unique=True)
    
    dob = models.DateField()
    gender = models.CharField(choices=GENDER_CHOICES)
    phone_num = models.CharField(blank=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True, null=True)
    referred_by = models.CharField(max_length=50, blank=True)
    emergency = models.BooleanField(default=False, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.hin:  
            while True:
                new_hin = generate_HIN()
                if not PatientProfile.all_objects.filter(hin=new_hin).exists():
                    self.hin = new_hin
                    break
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.firstname} {self.lastname}"
    
class SubaccountProfile(BaseModel):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subaccounts", null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subaccount_profile")
    
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    dob = models.DateField()
    gender = models.CharField(choices=GENDER_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.hin:  
            while True:
                new_hin = generate_HIN()
                if not SubaccountProfile.all_objects.filter(hin=new_hin).exists():
                    self.hin = new_hin
                    break
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.firstname} {self.lastname}"