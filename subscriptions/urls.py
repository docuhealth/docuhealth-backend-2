from django.urls import path

from .views import ListCreateSubscriptionPlanView

urlpatterns = [
    path('/plans', ListCreateSubscriptionPlanView.as_view(), name='create-subscription-plan'),
]