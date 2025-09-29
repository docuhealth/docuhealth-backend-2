from rest_framework import serializers

from .models import SubscriptionPlan
from .requests import create_plan

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    features = serializers.ListField(child=serializers.CharField())
    
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"
        read_only_fields = ["paystack_plan_id"]
        
    def create(self, validated_data):
        payload = {
            "name": validated_data["name"],
            "interval": validated_data["interval"],
            "amount": int(validated_data["price"] * 100),
            "description": validated_data["description"],
            "currency": "NGN",
            }
        
        paystack_plan_id = create_plan(payload)
        validated_data["paystack_plan_id"] = paystack_plan_id
        
        return super().create(validated_data)