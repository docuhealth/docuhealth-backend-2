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
    paystack_plan_id = models.CharField(max_length=100, blank=True, null=True) 
    features = models.JSONField(default=list)
    role = models.CharField(max_length=20, choices=[(User.Role.PATIENT, "Patient"), (User.Role.HOSPITAL, "Hospital")], default=User.Role.PATIENT)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.interval})"

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name="subscriptions")
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=True)
    
    paystack_subscription_code = models.CharField(max_length=200, blank=True, null=True)
    paystack_email_token = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
