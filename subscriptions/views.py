from rest_framework import generics

from drf_spectacular.utils import extend_schema

from .models import SubscriptionPlan
from .serializers import SubscriptionPlanSerializer

from core.models import User

@extend_schema(tags=["Subscriptions"])
class ListCreateSubscriptionPlanView(generics.ListCreateAPIView):
    serializer_class = SubscriptionPlanSerializer
    pagination_class = None
    # Add patient and hospital permission classes
    
    def get_queryset(self):
        user_role = self.request.user.role
        return SubscriptionPlan.objects.filter(role=user_role)
        