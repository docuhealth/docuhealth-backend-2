from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.timezone import now, timedelta

from cloudinary.models import CloudinaryField

from docuhealth2.utils.generate import generate_HIN, generate_otp, generate_staff_id
from docuhealth2.models import BaseModel

def default_notification_settings():
    return  {
            "sign_in": { "email": True, "push": True, "dashboard": False },
            "info_change": { "email": True, "push": False, "dashboard": True },
            "assessment_diagnosis": { "email": True, "push": True, "dashboard": False 
        }}

class Gender(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'
    UNKNOWN = 'unknown', 'Unknown'

class UserManager(BaseUserManager):
    def create(self, **extra_fields):
        email = extra_fields.get("email")
        password = extra_fields.pop("password", None)
        
        email = self.normalize_email(email)
        user = self.model(**extra_fields)
        if password:
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
        SUBACCOUNT = 'subaccount', 'Subaccount'
        HOSPITAL = 'hospital', 'Hospital'
        HOSPITAL_STAFF = 'hospital_staff', 'Hospital Staff'
        ADMIN = 'admin', 'Admin'
        PHARMACY = 'pharmacy', 'Pharmacy'
        PHARMACY_PARTNER = 'pharmacy_partner', 'Pharmacy Partner'
    
    email = models.EmailField(unique=True, blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    paystack_cus_code = models.CharField(max_length=200, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    
    objects = UserManager()
    
    class Meta:
        db_table = 'core_user'
    
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
        otp = generate_otp()
        expiry_time = timezone.now() + timedelta(minutes=expiry_minutes)

        otp, _ = cls.objects.update_or_create(
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
    
    class Meta:
        db_table = 'core_otp'
    
    def __str__(self):
        return self.otp
    
class UserProfileImage(models.Model):
    user = models.OneToOneField(User, related_name="profile_img", on_delete=models.SET_NULL, null=True, blank=True)
    image = CloudinaryField("profile_images/") 
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_userprofileimage'
    

class PatientProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    hin = models.CharField(max_length=20, unique=True)
    
    dob = models.DateField()
    gender = models.CharField(choices=Gender.choices)
    phone_num = models.CharField(blank=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True, null=True)
    
    street = models.CharField(max_length=120, blank=True, null=True)
    city = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=20, blank=True, null=True)
    
    nin_hash = models.CharField(max_length=128, blank=True, null=True)
    
    referred_by = models.CharField(max_length=50, blank=True)
    emergency = models.BooleanField(default=False, blank=True)
    id_card_generated = models.BooleanField(default=False)
    nin_verified = models.BooleanField(default=False)
    
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
        
    class Meta:
        db_table = 'patients_patientprofile'
        
    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"
    
class NINVerificationAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="nin_verification_attempts")
    nin_hash = models.CharField(max_length=128, blank=True, null=True)  # hashed NIN
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]
        db_table = 'patients_ninverificationattempt'
        
class SubaccountProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subaccount_profile")
    parent = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="subaccounts", null=True, blank=True)
    hin = models.CharField(max_length=20, unique=True)
    
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100, blank=True)
    dob = models.DateField()
    gender = models.CharField(choices=Gender.choices)
    
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
        
    class Meta:
        db_table = 'patients_subaccountprofile'
    
    def __str__(self):
        return f"{self.firstname} {self.lastname}"
    
    def generate_id_card(self):
        if self.id_card_generated:
            return
        
        self.id_card_generated = True
        self.save(update_fields=['id_card_generated'])
        
class HospitalStaffProfile(BaseModel):
    class StaffRole(models.TextChoices):
        DOCTOR = "doctor", "Doctor"
        NURSE = "nurse", "Nurse"
        RECEPTIONIST = "receptionist", "Receptionist"
        
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hospital_staff_profile")
    hospital = models.ForeignKey("organizations.HospitalProfile", on_delete=models.CASCADE, related_name="staff")
    
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    phone_no = models.CharField(max_length=20)
    gender = models.CharField(choices=Gender.choices)
    
    role = models.CharField(max_length=20, choices=StaffRole.choices)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    staff_id = models.CharField(max_length=20, unique=True)
    ward = models.ForeignKey("facility.HospitalWard", on_delete=models.SET_NULL, related_name='staff', null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.staff_id:
            self.staff_id = generate_staff_id(self.hospital.name, self.role)
        super().save(*args, **kwargs)
        
    class Meta:
        db_table = 'hospitals_hospitalstaffprofile'
    
    def __str__(self):
        return f"Doctor: {self.user.email} ({self.specialization})"
    
    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"

