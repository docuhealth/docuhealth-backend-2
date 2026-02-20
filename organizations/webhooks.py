from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from sentry_sdk import logger as sentry_logger

import hmac
import hashlib
import os
import json

from drf_spectacular.utils import extend_schema

from .webhookshandlers import handle_subscription_create, handle_charge_success, handle_invoice_create, handle_payment_failed, handle_invoice_update, handle_not_renew, handle_disable


PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_LIVE_SECRET_KEY")

@extend_schema(tags=["Subscriptions"])
class PaystackWebhookView(APIView):
    authentication_classes = []  
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        payload = request.body
        signature = request.headers.get('x-paystack-signature')
        
        hashed = hmac.new(
            PAYSTACK_SECRET_KEY.encode(),
            msg=payload,
            digestmod=hashlib.sha512
        ).hexdigest()
        
        if hashed != signature:
            return Response({"detail": "Invalid signature"}, status=403)
        
        event = json.loads(payload)
        event_type = event.get("event")
        data = event.get("data", {})
        
        sentry_logger.info(f"Received event: {event_type}", extra={"data": data})
        
        if event_type == "subscription.create":
            handle_subscription_create(data)
            
        elif event_type == "charge.success":
            handle_charge_success(data)
            
        elif event_type == "invoice.create":
            handle_invoice_create(data)
            
        elif event_type == "invoice.update":
            handle_invoice_update(data)
            
        elif event_type == "invoice.payment_failed":
            handle_payment_failed(data)
            
        elif event_type == "subscription.not_renew":
            handle_not_renew(data)
            
        elif event_type == "subscription.disable":
            handle_disable(data)

        return Response({"status": "ok"}, status=200)
