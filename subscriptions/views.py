from rest_framework import generics
from rest_framework.exceptions import ValidationError

from drf_spectacular.utils import extend_schema

from .models import SubscriptionPlan
from .serializers import SubscriptionPlanSerializer, SubscriptionSerializer

from core.models import User
from docuhealth2.permissions import IsAuthenticatedPatient, IsAuthenticatedHospital

from .requests import create_customer

@extend_schema(tags=["Subscriptions"])
class ListCreateSubscriptionPlanView(generics.ListCreateAPIView):
    serializer_class = SubscriptionPlanSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedPatient, IsAuthenticatedHospital]
    # Add patient and hospital permission classes
    
    def get_queryset(self):
        user_role = self.request.user.role
        return SubscriptionPlan.objects.filter(role=user_role)
    
@extend_schema(tags=["Subscriptions"])
class CreateSubscriptionView(generics.CreateAPIView):
        serializer_class = SubscriptionSerializer
        permission_classes = [IsAuthenticatedPatient, IsAuthenticatedHospital]
        
        def create(self, request, *args, **kwargs):
            plan = request.data.get("plan")
            user = request.user
            
            serializer = self.get_serializer(data={**request.data, 'user': user})
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save()
            
            paystack_cus_code = user.paystack_cus_code
            email = user.email
            if not paystack_cus_code:
                user.paystack_cus_code = create_customer({'email': email})
            
            
            
        