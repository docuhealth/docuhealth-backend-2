from django.utils.dateparse import parse_datetime
from django.db import transaction

from .models import Subscription, Transaction, SubscriptionPlan
from .requests import deactivate_paystack_subscription
from accounts.models import User

from sentry_sdk import logger as sentry_logger

def handle_subscription_create(data):
    sentry_logger.info("Creating subscription", extra={"data": data})
    try:
        with transaction.atomic():
            paystack_cus_code = data.get("customer", {}).get("customer_code")
            user = User.objects.get(paystack_cus_code=paystack_cus_code)
            subscription = Subscription.objects.get(user=user)
            
            old_sub_code = subscription.paystack_subscription_code
            new_plan_code = data.get("plan", {}).get("plan_code")
            
            subscription.plan = SubscriptionPlan.objects.get(paystack_plan_code=new_plan_code)
            subscription.status = Subscription.SubscriptionStatus.ACTIVE
            subscription.paystack_subscription_code = data.get("subscription_code")
            subscription.next_payment_date = parse_datetime(data.get("next_payment_date"))
            subscription.authorization_code = data.get("authorization", {}).get("authorization_code")
            
            subscription.save(update_fields=['status', 'paystack_subscription_code', 'next_payment_date', 'authorization_code', 'plan'])
            
            sentry_logger.info(f"Subscription activated for user {user.id}", extra={
                "subscription_id": subscription.id,
                "paystack_code": paystack_cus_code
            })
            
        if old_sub_code and old_sub_code != subscription.paystack_subscription_code:
            deactivate_paystack_subscription(old_sub_code)
        
    except (User.DoesNotExist, Subscription.DoesNotExist) as e:
        sentry_logger.error(f"Subscription creation failed: User/Sub not found for code {paystack_cus_code}", exc_info=True)
    except Exception as e:
        sentry_logger.error(f"Subscription creation failed: {e}", exc_info=True)                                                            
    
def handle_charge_success(data):
    try:
        with transaction.atomic():
            paystack_cus_code = data.get("customer", {}).get("customer_code")
            user = User.objects.get(paystack_cus_code=paystack_cus_code)
            subscription = Subscription.objects.select_for_update().get(user=user)
            
            subscription.status = Subscription.SubscriptionStatus.ACTIVE
            subscription.last_payment_date = parse_datetime(data.get("paid_at"))
            subscription.save(update_fields=['status', 'last_payment_date'])
            
            Transaction.objects.update_or_create(
                reference=data.get("reference"),
                user=user,
                defaults={
                "amount": data.get("amount") / 100, 
                "status": Transaction.Status.SUCCESS,
                "created_at": parse_datetime(data.get("paid_at"))}
            )
            
    except (User.DoesNotExist, Subscription.DoesNotExist) as e:
        sentry_logger.error(f"Charge success failed: User/Sub not found for code {paystack_cus_code}", exc_info=True)
    except Exception as e:
        sentry_logger.error(f"Charge success failed: {e}", exc_info=True)
    
def handle_invoice_create(data):
    # TODO: Send notifications
    pass
    
def handle_invoice_update(data):
    try:
        paystack_cus_code = data.get("customer", {}).get("customer_code")
        user = User.objects.get(paystack_cus_code=paystack_cus_code)
        subscription = Subscription.objects.get(user=user)
        
        if data.get("status") == "success":
            subscription.next_payment_date = parse_datetime(data.get("next_payment_date"))
        
        subscription.save(update_fields=['next_payment_date'])
        
        sentry_logger.info(f"Invoice updated for user {user.id}", extra={
            "subscription_id": subscription.id,
            "paystack_code": paystack_cus_code
        })
        
    except (User.DoesNotExist, Subscription.DoesNotExist) as e:
        sentry_logger.error(f"Invoice update failed: User/Sub not found for code {paystack_cus_code}", exc_info=True)
    except Exception as e:
        sentry_logger.error(f"Invoice update failed: {e}", exc_info=True)
    
def handle_payment_failed(data):
    try:
        paystack_cus_code = data.get("customer", {}).get("customer_code")
        user = User.objects.get(paystack_cus_code=paystack_cus_code)
        subscription = Subscription.objects.get(user=user)
        
        subscription.status = Subscription.SubscriptionStatus.PAST_DUE
        subscription.save(update_fields=['status'])
        
        sentry_logger.info(f"Payment failed for user {user.id}", extra={
            "subscription_id": subscription.id,
            "paystack_code": paystack_cus_code
        })
    
    except (User.DoesNotExist, Subscription.DoesNotExist) as e:
        sentry_logger.error(f"Payment failed handler error: User/Sub not found for code {paystack_cus_code}", exc_info=True)
    except Exception as e:
        sentry_logger.error(f"Payment failed handler error : {e}", exc_info=True)
    
def handle_not_renew(data):
    try:
        paystack_cus_code = data.get("customer", {}).get("customer_code")
        user = User.objects.get(paystack_cus_code=paystack_cus_code)
        subscription = Subscription.objects.get(user=user)
        
        subscription.will_renew = False
        subscription.save(update_fields=['will_renew'])
        
        sentry_logger.info(f"Sub not renew for user {user.id}", extra={
            "subscription_id": subscription.id,
            "paystack_code": paystack_cus_code
        })
    
    except (User.DoesNotExist, Subscription.DoesNotExist) as e:
        sentry_logger.error(f"Sub Not renew handler error: User/Sub not found for code {paystack_cus_code}", exc_info=True)
    except Exception as e:
        sentry_logger.error(f"Sub Not renew handler error : {e}", exc_info=True)
    
def handle_disable(data):
    try:
        paystack_cus_code = data.get("customer", {}).get("customer_code")
        user = User.objects.get(paystack_cus_code=paystack_cus_code)
        subscription = Subscription.objects.get(user=user)
        
        subscription.status = Subscription.SubscriptionStatus.INACTIVE
        subscription.save(update_fields=['status'])
        
        sentry_logger.info(f"Sub disabled for user {user.id}", extra={
            "subscription_id": subscription.id,
            "paystack_code": paystack_cus_code
        })
        
    except (User.DoesNotExist, Subscription.DoesNotExist) as e:
        sentry_logger.error(f"Sub disable handler error: User/Sub not found for code {paystack_cus_code}", exc_info=True)
    except Exception as e:
        sentry_logger.error(f"Sub disable handler error : {e}", exc_info=True)
    
    
    
