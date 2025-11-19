from django.db import models
from core.models import User
from django.utils import timezone
import secrets
import hashlib

from datetime import timedelta

from docuhealth2.models import BaseModel
from docuhealth2.utils.generate import generate_HIN, generate_staff_id

from core.models import Gender
from patients.models import PatientProfile

def default_notification_settings():
    return  {
            "sign_in": { "email": True, "push": True, "dashboard": False },
            "info_change": { "email": True, "push": False, "dashboard": True },
            "assessment_diagnosis": { "email": True, "push": True, "dashboard": False 
        }}

class HospitalInquiry(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONTACTED = 'contacted', 'Contacted'
        CLOSED = 'closed', 'Closed'
    
    name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    def __str__(self):
        return f"{self.name} ({self.contact_email})"
    
class HospitalVerificationRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
    
    inquiry = models.OneToOneField(HospitalInquiry, on_delete=models.CASCADE, related_name="verification_request")
    official_email = models.EmailField()
    documents = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING) 
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.inquiry.name} ({self.official_email})"
    
def default_expiry():
    return timezone.now() + timedelta(days=7)

def get_token():
    return secrets.token_urlsafe(32)

def hash_token(raw_token: str):
    return hashlib.sha256(raw_token.encode()).hexdigest()
    
class VerificationToken(BaseModel):
    verification_request = models.OneToOneField(HospitalVerificationRequest, on_delete=models.CASCADE, related_name="verification_token")
    token = models.CharField(max_length=255)
    expiry = models.DateTimeField(default=default_expiry)
    verified = models.BooleanField(default=False)
    
    @classmethod
    def generate_token(cls, verification_request):
        token = get_token()
        hashed = hash_token(token)
        
        token_instance, _ = cls.objects.update_or_create(verification_request=verification_request, defaults={"token": hashed})
        
        return token
    
    def is_expired(self):
        return timezone.now() > self.expiry

    def verify(self, token):
        if self.verified:
            return False, "This token has already used"

        if self.is_expired():
            return False, "This token has expired"

        if self.token != hash_token(token):
            return False, "Invalid token"

        self.verified = True
        self.save(update_fields=["verified"])
        return True, "Token verified successfully"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["verification_request"], name="unique_verification_per_request")
        ]
    
    def __str__(self):
        return self.token

class HospitalProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hospital_profile")
    hin = models.CharField(max_length=20, unique=True)
    
    name = models.CharField(max_length=100, blank=True)
    
    street = models.CharField(max_length=120, blank=True, null=True)
    city = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=20, blank=True, null=True)
    
    notification_settings = models.JSONField(default=default_notification_settings)
    
    paystack_cus_code = models.CharField(max_length=200, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.hin:  
            while True:
                new_hin = generate_HIN()
                if not HospitalProfile.all_objects.filter(hin=new_hin).exists():
                    self.hin = new_hin
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"HospitalAdmin: {self.name} hospital,  ({self.user.email})"
    
class HospitalWard(BaseModel):
    name = models.CharField(max_length=100)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="wards")
    total_beds = models.IntegerField()
    
    def __str__(self):
        return f"Ward {self.name}"
    
    @property
    def available_beds(self):
        return self.beds.filter(status="available").count()

class HospitalStaffProfile(BaseModel):
    class StaffRole(models.TextChoices):
        DOCTOR = "doctor", "Doctor"
        NURSE = "nurse", "Nurse"
        RECEPTIONIST = "receptionist", "Receptionist"
        
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hospital_staff_profile")
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="staff")
    
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    phone_no = models.CharField(max_length=20)
    gender = models.CharField(choices=Gender.choices)
    
    role = models.CharField(max_length=20, choices=StaffRole.choices)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    staff_id = models.CharField(max_length=20, unique=True)
    ward = models.ForeignKey(HospitalWard, on_delete=models.SET_NULL, related_name='staff', null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.staff_id:
            self.staff_id = generate_staff_id(self.hospital.name, self.role)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Doctor: {self.user.email} ({self.specialization})"
    
    
class HospitalPatientActivity(BaseModel):
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE)
    staff = models.ForeignKey(HospitalStaffProfile, on_delete=models.SET_NULL, null=True)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)

    action = models.CharField(max_length=100)  

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hospital', 'staff', 'created_at']),
        ]
        
class WardBed(BaseModel):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        OCCUPIED = "occupied", "Occupied"
        REQUESTED = "requested", "Requested"
        
    ward = models.ForeignKey(HospitalWard, on_delete=models.CASCADE, related_name="beds")
    bed_number = models.IntegerField()  
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    def __str__(self):
        return f"{self.ward.name} - Bed {self.bed_number}"
    
    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE
    
class Admission(BaseModel):
    class Status(models.TextChoices):
        PENDING= "pending", "Pending"
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"
        DISCHARGED = "discharged", "Discharged"
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="admissions")
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.SET_NULL, related_name="admissions", null=True)
    staff = models.ForeignKey(HospitalStaffProfile, on_delete=models.SET_NULL, related_name="admissions", null=True)
    
    ward = models.ForeignKey(HospitalWard, on_delete=models.SET_NULL, related_name="admissions", null=True)
    bed = models.ForeignKey(WardBed, on_delete=models.SET_NULL, related_name="admissions", null=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    request_date = models.DateTimeField(auto_now_add=True)
    admission_date = models.DateTimeField(null=True, blank=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Admission for {self.patient.full_name} at {self.hospital.name}"
    
    

