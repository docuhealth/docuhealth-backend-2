from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
import os
from rest_framework.response import Response
from rest_framework import status

from dotenv import load_dotenv
load_dotenv()

class BrevoEmailService:
    def __init__(self):
        self.configuration = Configuration()
        self.configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")
        self.api_instance = TransactionalEmailsApi(ApiClient(self.configuration))

    def send(self, subject: str, body: str, recipient: str, is_html=False):
        sender_email="docuhealthservice@gmail.com"
        sender_name="DocuHealth Services"
        
        content_field = "html_content" if is_html else "text_content"

        email_data = {
            "to": [{"email": recipient}],
            "sender": {"email": sender_email, "name": sender_name},
            "subject": subject,
            content_field: body,
        }
        
        email = SendSmtpEmail(**email_data)
        
        try:
            self.api_instance.send_transac_email(email)
        
        except Exception as e:
            print(f"Email send failed: {e}")
            return Response({"detail": str(e), "status": "error"}, status=status.HTTP_400_BAD_REQUEST)