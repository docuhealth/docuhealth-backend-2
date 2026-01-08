from django.db import models
from django.utils import timezone
from django.db import models

from datetime import timedelta
import secrets
import hashlib

from docuhealth2.utils.generate import generate_HIN
from docuhealth2.models import BaseModel

from accounts.models import User, default_notification_settings

from docuhealth2.models import BaseModel


class HospitalProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hospital_profile")
    hin = models.CharField(max_length=20, unique=True)
    
    name = models.CharField(max_length=100, blank=True)
    
    street = models.CharField(max_length=120, blank=True, null=True)
    city = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=20, blank=True, null=True)
    
    notification_settings = models.JSONField(default=default_notification_settings)
    
    def save(self, *args, **kwargs):
        if not self.hin:  
            while True:
                new_hin = generate_HIN()
                if not HospitalProfile.all_objects.filter(hin=new_hin).exists():
                    self.hin = new_hin
                    break
        super().save(*args, **kwargs)
        
    class Meta:
        db_table = 'hospitals_hospitalprofile'

    def __str__(self):
        return f"HospitalAdmin: {self.name} hospital,  ({self.user.email})"
    
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
    
    class Meta:
        db_table = 'hospitals_hospitalinquiry'
    
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
    
    class Meta:
        db_table = 'hospitals_hospitalverificationrequest'
    
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
        db_table = 'hospitals_verificationtoken'
    
    def __str__(self):
        return self.token
    
class SubscriptionPlan(models.Model):
    class Intervals(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"
        WEEKLY = "weekly", "Weekly"     
        
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    description = models.TextField()
    interval = models.CharField(max_length=20, choices=Intervals.choices)
    paystack_plan_code = models.CharField(max_length=100, blank=True, null=True) 
    features = models.JSONField(default=list)
    role = models.CharField(max_length=20, choices=[(User.Role.PATIENT, "Patient"), (User.Role.HOSPITAL, "Hospital")], default=User.Role.PATIENT)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions_subscriptionplan'

    def __str__(self):
        return f"{self.name} ({self.interval})"

class Subscription(models.Model):
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        PAST_DUE = "past_due", "Past_Due"
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name="subscriptions")
    paystack_subscription_code = models.CharField(max_length=200, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.INACTIVE)
    will_renew = models.BooleanField(default=True)
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    next_payment_date = models.DateTimeField(blank=True, null=True)
    last_payment_date = models.DateTimeField(blank=True, null=True)
    
    authorization_code = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions_subscription'

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
    
class PaystackCustomer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="paystack_customer")
    customer_code = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions_paystackcustomer'
