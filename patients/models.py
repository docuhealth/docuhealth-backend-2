from django.db import models
from core.models import User

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
    middlename = models.CharField(max_length=100, blank=True, null=True)
    referred_by = models.CharField(max_length=50, blank=True)
    emergency = models.BooleanField(default=False, blank=True)
    
    def __str__(self):
        return f"{self.firstname} {self.lastname}"
    
class Subaccount(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subaccounts", null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subaccount_profile")
    
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    dob = models.DateField()
    gender = models.CharField(choices=GENDER_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.firstname} {self.lastname}"