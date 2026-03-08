from django.db.models import Count, Sum, Q
from django.db import transaction
from django.db.models.functions import TruncMonth

from rest_framework import generics
from rest_framework.response import Response

from organizations.models import Transaction, Subscription
from accounts.models import User

from docuhealth2.permissions import IsAuthenticatedDHAdmin

from drf_spectacular.utils import extend_schema

@extend_schema(tags=["DH Admin"], summary="Get admin dashboard metrics and trends")
class AdminDashboard(generics.GenericAPIView): # TODO: Cache results for efficiency
    permission_classes = [IsAuthenticatedDHAdmin]
    
    @staticmethod
    def format_trend(queryset):
        return [{"month": item['month'].strftime('%Y-%m'), "value": item['value']} for item in queryset]

    def get(self, request):
        summary_metrics = User.objects.filter(
            is_active=True, 
            role__in=[User.Role.HOSPITAL, User.Role.PATIENT]
            ).aggregate(
                total_users=Count('id'),
                total_hospitals=Count('hospital_profile', distinct=True),
                total_patients=Count('patient_profile', distinct=True),
                
                total_subscribed_users=Count(
                    'subscription',
                    filter=Q(subscription__status=Subscription.SubscriptionStatus.ACTIVE), 
                    distinct=True
                ), 
                
                total_revenue=Sum('transactions__amount'),
                
                patients_with_sub=Count(
                    'id', 
                    filter=Q(patient_profile__subaccounts__isnull=False),
                    distinct=True
                ),
                
                patients_without_sub=Count(
                    'id', 
                    filter=Q(patient_profile__subaccounts__isnull=True),
                    distinct=True
                )
            )

        revenue_trend = (
            Transaction.objects
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(value=Sum('amount'))
            .order_by('month')
        )

        user_trend = (
            User.objects.filter(role__in=[User.Role.HOSPITAL, User.Role.PATIENT], is_active=True)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(value=Count('id'))
            .order_by('month')
        )
        
        subscription_trend = (
            Subscription.objects
            .filter(status=Subscription.SubscriptionStatus.ACTIVE)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(value=Count('id'))
            .order_by('month')
        )
        
        response_data = {
            "summary": {
                "total_users": summary_metrics['total_users'],
                "total_revenue": summary_metrics['total_revenue'] or 0,
                "total_hospitals": summary_metrics['total_hospitals'],
                "total_individuals": summary_metrics['total_patients'],
                "total_subscribed_users": summary_metrics['total_subscribed_users'],
            },
            
            "charts": {
                "revenue_overview": self.format_trend(revenue_trend),
                "registered_users": self.format_trend(user_trend),
                "subscribed_users": self.format_trend(subscription_trend),
                "sub_account_stats": [
                    {"label": "With subaccount", "value": summary_metrics['patients_with_sub']},
                    {"label": "Without subaccount", "value": summary_metrics['patients_without_sub']},
                ]
            }
        }

        return Response(response_data)