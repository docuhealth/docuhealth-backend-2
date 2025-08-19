from django.db import models
from django.conf import settings

class PatientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dob = models.DateField()
    gender = models.Choices(choices=['male', 'female', 'other', 'unknown'])
    phone_num = models.CharField(blank=True)
    
