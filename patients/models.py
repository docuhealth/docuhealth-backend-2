from django.db import models
from django.conf import settings

from core.models import User
from docuhealth2.utils.generate import generate_HIN

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
    ('unknown', 'Unknown'),
]

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    dob = models.DateField()
    gender = models.CharField(choices=GENDER_CHOICES)
    phone_num = models.CharField(blank=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    referred_by = models.CharField(max_length=50, blank=True)
    emergency = models.BooleanField(default=False, blank=True)
    
class Subaccount(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subaccounts")
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    dob = models.DateField()
    gender = models.CharField(choices=GENDER_CHOICES)
    hin = models.CharField(max_length=20, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)