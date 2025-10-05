from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .models import SubscriptionPlan
from .serializers import SubscriptionPlanSerializer, SubscriptionSerializer

from core.models import User
from docuhealth2.permissions import IsAuthenticatedPatient, IsAuthenticatedHospital

from .requests import create_customer, initialize_transaction

@extend_schema(tags=["Subscriptions"])
class ListCreateSubscriptionPlanView(generics.ListCreateAPIView):
    serializer_class = SubscriptionPlanSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedPatient] # TODO: Update to include hospitals
    
    def get_queryset(self):
        user_role = self.request.user.role
        return SubscriptionPlan.objects.filter(role=user_role)
    
@extend_schema(tags=["Subscriptions"])
class CreateSubscriptionView(generics.CreateAPIView):
        serializer_class = SubscriptionSerializer
        permission_classes = [IsAuthenticatedPatient] # TODO: Update to include hospitals
        
        def get_serializer_context(self):
            context = super().get_serializer_context()
            context["user"] = self.request.user
            return context
        
        def create(self, request, *args, **kwargs):
            user = request.user
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save()
            
            plan = subscription.plan
            paystack_cus_code = user.paystack_cus_code
            email = user.email
            
            if not paystack_cus_code:
                paystack_cus_code = create_customer({"email": email})
                user.paystack_cus_code = paystack_cus_code
                user.save(update_fields=['paystack_cus_code'])
                
            transaction_payload = {
                "email": email,
                "amount": plan.price * 100,
                "plan": plan.paystack_plan_code 
            }
            
            auth_url = initialize_transaction(transaction_payload)
            
            response_data = self.get_serializer(subscription).data
            response_data["authorization_url"] = auth_url
            return Response(response_data, status=status.HTTP_201_CREATED) 
            
                
            
            
            
            
        