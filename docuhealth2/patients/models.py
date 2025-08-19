from django.db import models
from django.conf import settings

class PatientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dob = models.DateField()
    gender = models.Choices(choices=['male', 'female', 'other', 'unknown'])
    phone_num = models.CharField(blank=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    referred_by = models.CharField(max_length=50, blank=True)
    emergency = models.BooleanField(default=False, blank=True)
    
    
