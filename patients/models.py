from django.db import models
from core.models import User

from docuhealth2.models import BaseModel
from docuhealth2.utils.generate import generate_HIN

def default_notification_settings():
    return  {
            "sign_in": { "email": True, "push": True, "dashboard": False },
            "info_change": { "email": True, "push": False, "dashboard": True },
            "assessment_diagnosis": { "email": True, "push": True, "dashboard": False 
        }}

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
    ('unknown', 'Unknown'),
]

class PatientProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    hin = models.CharField(max_length=20, unique=True)
    
    dob = models.DateField()
    gender = models.CharField(choices=GENDER_CHOICES)
    phone_num = models.CharField(blank=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True, null=True)
    
    street = models.CharField(max_length=120, blank=True, null=True)
    city = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=20, blank=True, null=True)
    
    referred_by = models.CharField(max_length=50, blank=True)
    emergency = models.BooleanField(default=False, blank=True)
    id_card_generated = models.BooleanField(default=False)
    
    paystack_cus_code = models.CharField(max_length=200, blank=True, null=True)
    
    notification_settings = models.JSONField(default=default_notification_settings)
    
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
    
    def toggle_emergency(self):
        self.emergency = not self.emergency
        self.save(update_fields=['emergency'])
        
    def generate_id_card(self):
        if self.id_card_generated:
            return
        
        self.id_card_generated = True
        self.save(update_fields=['id_card_generated'])
    
class SubaccountProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subaccount_profile")
    parent = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="subaccounts", null=True, blank=True)
    hin = models.CharField(max_length=20, unique=True)
    
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    dob = models.DateField()
    gender = models.CharField(choices=GENDER_CHOICES)
    
    street = models.CharField(max_length=120, blank=True, null=True)
    city = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=20, blank=True, null=True)
    
    id_card_generated = models.BooleanField(default=False)
    
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
    
    def generate_id_card(self):
        if self.id_card_generated:
            return
        
        self.id_card_generated = True
        self.save(update_fields=['id_card_generated'])