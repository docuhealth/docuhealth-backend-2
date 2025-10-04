from rest_framework import serializers

from .models import SubscriptionPlan, Subscription
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
        
        return super().create(validated_data) # TODO: Move to view
    
class SubscriptionSerializer(serializers.ModelSerializer):
    plan = serializers.SlugRelatedField(slug_field="paystack_plan_code", queryset=SubscriptionPlan.objects.all())
    
    class Meta:
        model = Subscription
        fields = "__all__"
        read_only_fields = ["user", "paystack_subscription_code", "status", "will_renew", "start_date", "end_date", "next_payment_date", "last_payment_date", "authorization_code", "created_at", "updated_at"]
        
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        
        plan = validated_data.get("plan")
        user = validated_data.get("user")
        
        if plan.role != user.role:
            raise serializers.ValidationError("This plan is not available for your role.")
        
        # if not plan.is_active:
        #     raise serializers.ValidationError("Current plan is not active")
        
        return validated_data
        
    def create(self, validated_data):
       user = validated_data.get("user")
       plan = validated_data.get("plan")
       
       subscription = Subscription.objects.create(user=user, plan=plan)

    #    watermelon comment
       
       return subscription