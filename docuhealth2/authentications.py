from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth.hashers import check_password
from organizations.models import Client
from accounts.models import User

class ClientHeaderAuthentication(BaseAuthentication):
    def authenticate(self, request):
        client_id = request.headers.get('X-Client-ID')
        client_secret = request.headers.get('X-Client-Secret')

        if not client_id or not client_secret:
            return None 

        try:
            client = Client.objects.select_related('user').get(client_id=client_id, is_active=True)
        except Client.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid Credentials')

        if not check_password(client_secret, client.client_secret_hash):
            raise exceptions.AuthenticationFailed('Invalid Credentials')

        if client.user.role != User.Role.PHARMACY_PARTNER:
             raise exceptions.AuthenticationFailed('Not a Partner account')

        return (client.user, client)