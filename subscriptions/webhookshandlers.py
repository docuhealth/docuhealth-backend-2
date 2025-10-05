from django.utils.dateparse import parse_datetime

from .models import Subscription
from core.models import User

def handle_subscription_create(data):
    paystack_cus_code = data.get("customer", {}).get("customer_code")
    user = User.objects.get(paystack_cus_code=paystack_cus_code)
    subscription = Subscription.objects.get(user=user)
    
    subscription.status = Subscription.SubscriptionStatus.ACTIVE
    subscription.paystack_subscription_code = data.get("subscription_code")
    subscription.next_payment_date = parse_datetime(data.get("next_payment_date"))
    subscription.authorization_code = data.get("authorization", {}).get("authorization_code")
    # subscription.start_date = data
    
    subscription.save(update_fields=['status', 'paystack_subscription_code', 'next_payment_date', 'authorization_code'])
    
    print(subscription)
    
def handle_charge_success(data):
    paystack_cus_code = data.get("customer", {}).get("customer_code")
    user = User.objects.get(paystack_cus_code=paystack_cus_code)
    subscription = Subscription.objects.get(user=user)
    
    subscription.status = Subscription.SubscriptionStatus.ACTIVE
    subscription.last_payment_date = parse_datetime(data.get("paid_at"))
    subscription.save(update_fields=['status', 'last_payment_date'])
    
    print(subscription)
    
def handle_invoice_create(data):
    # TODO: Send notifications
    pass
    
def handle_invoice_update(data):
    paystack_cus_code = data.get("customer", {}).get("customer_code")
    user = User.objects.get(paystack_cus_code=paystack_cus_code)
    subscription = Subscription.objects.get(user=user)
    
    if data.get("status") == "success":
       subscription.next_payment_date = parse_datetime(data.get("next_payment_date"))
       
    subscription.save(update_fields=['next_payment_date'])
    
    print(subscription)
    
def handle_payment_failed(data):
    paystack_cus_code = data.get("customer", {}).get("customer_code")
    user = User.objects.get(paystack_cus_code=paystack_cus_code)
    subscription = Subscription.objects.get(user=user)
    
    subscription.status = Subscription.SubscriptionStatus.PAST_DUE
    subscription.save(update_fields=['status'])
    
    print(subscription)
    
def handle_not_renew(data):
    paystack_cus_code = data.get("customer", {}).get("customer_code")
    user = User.objects.get(paystack_cus_code=paystack_cus_code)
    subscription = Subscription.objects.get(user=user)
    
    subscription.will_renew = False
    subscription.save(update_fields=['will_renew'])
    
    print(subscription)
    
def handle_disable(data):
    paystack_cus_code = data.get("customer", {}).get("customer_code")
    user = User.objects.get(paystack_cus_code=paystack_cus_code)
    subscription = Subscription.objects.get(user=user)
    
    subscription.status = Subscription.SubscriptionStatus.INACTIVE
    subscription.save(update_fields=['status'])
    
    print(subscription)
    
    
