from rest_framework import serializers

class SummarySerializer(serializers.Serializer):
    total_users = serializers.IntegerField(help_text="Total active hospitals and patients.")
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Sum of all successful transactions.")
    total_hospitals = serializers.IntegerField(help_text="Count of unique hospital profiles.")
    total_individuals = serializers.IntegerField(help_text="Count of unique patient profiles.")
    total_subscribed_users = serializers.IntegerField(help_text="Count of users with an active subscription.")

class TrendDataSerializer(serializers.Serializer):
    month = serializers.CharField(help_text="Month formatted as YYYY-MM.")
    value = serializers.IntegerField(help_text="The aggregate count or sum for that month.")

class StateFunnelSerializer(serializers.Serializer):
    state = serializers.CharField(help_text="State name (normalized where possible).")
    value = serializers.IntegerField(help_text="Number of registrations in this state.")

class SubAccountStatSerializer(serializers.Serializer):
    label = serializers.CharField(help_text="'With subaccount' or 'Without subaccount'.")
    value = serializers.IntegerField()

class ChartsSerializer(serializers.Serializer):
    revenue_overview = TrendDataSerializer(many=True)
    registered_users = TrendDataSerializer(many=True)
    subscribed_users = TrendDataSerializer(many=True)
    states = StateFunnelSerializer(many=True)
    sub_account_stats = SubAccountStatSerializer(many=True)

class AdminDashboardSerializer(serializers.Serializer):
    summary = SummarySerializer()
    charts = ChartsSerializer()