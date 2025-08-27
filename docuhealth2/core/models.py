from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
from utils.random_code import generate_HIN

role_choices = [
        ('patient', 'Patient'),
        ('hospital', 'Hospital'),
        ('admin', 'Admin'),
        ('pharmacy', 'Pharmacy'),
    ]

def default_notification_settings():
    return  {
            "sign_in": { "email": True, "push": True, "dashboard": False },
            "info_change": { "email": True, "push": False, "dashboard": True },
            "assessment_diagnosis": { "email": True, "push": True, "dashboard": False 
            }}

class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        if not password:
            raise ValueError("Users must have a password")
        
        while True:
            hin = generate_HIN()
            if not User.objects.filter(hin=hin).exists():
                extra_fields['hin'] = hin
                break

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

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
    
    hin = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    
    notification_settings = models.JSONField(default=default_notification_settings)
    
    street = models.CharField(max_length=120)
    city = models.CharField(max_length=20)
    state = models.CharField(max_length=20)
    country = models.CharField(max_length=20)
    house_no = models.CharField(max_length=10, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.email} ({self.role})"

def default_expiry():
    return timezone.now() + timedelta(minutes=10)

class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="otp")
    otp = models.CharField(max_length=6)  
    expiry = models.DateTimeField(default=default_expiry)
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
