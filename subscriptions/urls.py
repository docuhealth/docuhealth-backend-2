from django.urls import path

from .views import ListCreateSubscriptionPlanView, CreateSubscriptionView
from .webhooks import PaystackWebhookView

urlpatterns = [
    path('/plans', ListCreateSubscriptionPlanView.as_view(), name='create-subscription-plan'),
    path('/subscribe', CreateSubscriptionView.as_view(), name='subscribe to plan'),
    path('/paystack_webhook', PaystackWebhookView.as_view(), name='paystack-webhook'),
]