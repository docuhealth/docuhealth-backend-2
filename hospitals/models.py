from django.db import models
from core.models import User
from django.utils import timezone
import secrets
import hashlib

from datetime import timedelta

from docuhealth2.models import BaseModel
from docuhealth2.utils.generate import generate_HIN

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
    
    inquiry = models.ForeignKey(HospitalInquiry, on_delete=models.CASCADE, related_name="verification_requests")
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
    
    firstname = models.CharField(max_length=100, blank=True)
    lastname = models.CharField(max_length=100, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.hin:  
            while True:
                new_hin = generate_HIN()
                if not HospitalProfile.all_objects.filter(hin=new_hin).exists():
                    self.hin = new_hin
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"HospitalAdmin: {self.firstname} {self.lastname} ({self.user.email})"


class DoctorProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="doctors")
    doc_id = models.CharField(max_length=20, unique=True)
    
    firstname = models.CharField(max_length=100, blank=True)
    lastname = models.CharField(max_length=100, blank=True)
    
    specialization = models.CharField(max_length=100, blank=True)
    license_no = models.CharField(max_length=50, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.doc_id:  
            while True:
                new_doc_id = generate_HIN()
                if not DoctorProfile.all_objects.filter(doc_id=new_doc_id).exists():
                    self.doc_id = new_doc_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Doctor: {self.user.email} ({self.specialization})"
