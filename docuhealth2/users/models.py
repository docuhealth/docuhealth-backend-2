from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
from ..patients.models import PatientProfile
import uuid
from docuhealth2.utils.random_code import unique_HIN

role_choices = [
        ('patient', 'Patient'),
        ('hospital', 'Hospital'),
        ('admin', 'Admin'),
        ('pharmacy', 'Pharmacy'),
    ]

default_notification_settings = {
  "sign_in": { "email": True, "push": True, "dashboard": False },
  "info_change": { "email": True, "push": False, "dashboard": True },
  "assessment_diagnosis": { "email": True, "push": True, "dashboard": False }
}

class OTP(models.Model):
    user = models.OneToOneField(AbstractUser, on_delete=models.CASCADE, related_name="otps")
    otp = models.CharField(max_length=6)  
    expiry = models.DateTimeField(default=lambda: timezone.now() + timedelta(minutes=10))
    verified = models.BooleanField(default=False)
    
    @classmethod
    def generate_otp(cls, user, expiry_minutes=10):
        """Create or replace OTP for a user"""
        otp = str(random.randint(100000, 999999))  
        expiry_time = timezone.now() + timedelta(minutes=expiry_minutes)

        otp, created = cls.objects.update_or_create(
            user=user,
            defaults={
                "otp": otp,
                "expiry": expiry_time,
                "verified": False
            }
        )
        return otp

    def is_expired(self):
        return timezone.now() > self.expiry

    def verify(self, otp):
        if self.verified:
            return False, "OTP already used"

        if self.is_expired():
            return False, "This OTP has expired"

        if self.otp != otp:
            return False, "Invalid OTP"

        self.verified = True
        self.save(update_fields=["verified"])
        return True, "OTP verified successfully"
    
    def __str__(self):
        return self.otp

class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        if not password:
            raise ValueError("Users must have a password")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        role = extra_fields.get("role")
        if role == User.Role.PATIENT:
            PatientProfile.objects.create(user=user)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)
    
class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        PATIENT = 'patient', 'Patient'
        HOSPITAL = 'hospital', 'Hospital'
        ADMIN = 'admin', 'Admin'
        PHARMACY = 'pharmacy', 'Pharmacy'
    
    hin = models.CharField(max_length=20, unique=True, default=unique_HIN)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    
    notification_settings = models.JSONField(default=default_notification_settings)
    
    street = models.CharField(max_length=120)
    city = models.CharField(max_length=20)
    state = models.CharField(max_length=20)
    country = models.CharField(max_length=20)
    
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['email']
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.email} ({self.role})"



# hospitals/models.py
class HospitalProfile(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    logo = models.ImageField(upload_to="hospital_logos/")
    departments = models.JSONField(default=list)
    # hospital-specific fields...

# pharmacies/models.py
class PharmacyProfile(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    inventory = models.JSONField(default=list)
    # pharmacy-specific fields...
