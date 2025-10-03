# subscriptions/models.py
from django.db import models
from django.utils import timezone
from core.models import User  

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

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
    
class PaystackCustomer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="paystack_customer")
    customer_code = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
