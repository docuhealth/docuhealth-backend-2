# users/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from ..models import User

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD  # ensures we use email

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        role = self.context["request"].data.get("role")

        if not email or not password or not role:
            raise serializers.ValidationError(_("Email, password and role required."))

        try:
            user = User.objects.get(email=email, role=role, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError(_("Invalid credentials."))

        user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user:
            raise serializers.ValidationError(_("Invalid password."))

        # normal JWT data
        data = super().validate(attrs)

        # add extra claims
        data["role"] = user.role
        data["email"] = user.email
        data["HIN"] = user.HIN

        # here you can trigger your notifications
        # send_login_email(user)
        # send_in_app_notification(user)

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        token["role"] = user.role
        token["email"] = user.email
        token["HIN"] = user.HIN
        return token
