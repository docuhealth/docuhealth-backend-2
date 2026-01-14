from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.hashers import check_password
from organizations.models import PharmacyClient

class PharmacyClientHeaderAuthentication(BaseAuthentication):
    def authenticate(self, request):
        client_id = request.headers.get('X-Pharmacy-ID')
        client_secret = request.headers.get('X-Pharmacy-Secret')

        if not client_id or not client_secret:
            return None 

        try:
            pharmacy = PharmacyClient.objects.get(client_id=client_id, is_active=True)
        except PharmacyClient.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid Pharmacy Credentials')

        if not check_password(client_secret, pharmacy.client_secret_hash):
            raise exceptions.AuthenticationFailed('Invalid Pharmacy Credentials')

        return (None, pharmacy)