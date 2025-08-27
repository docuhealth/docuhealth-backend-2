from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenVerifySerializer

from datetime import timedelta

class PasswordResetToken(Token):
    token_type = "token"   
    lifetime = timedelta(minutes=10) 

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token["purpose"] = "password_reset"
        return token
        
class PasswordResetTokenAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        if validated_token.get("purpose") != "password_reset":
            raise InvalidToken("Password reset token required")

        return super().get_user(validated_token)

