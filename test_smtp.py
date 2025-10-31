import smtplib
from dotenv import load_dotenv
import os

load_dotenv()

smtp_server = "smtp-relay.brevo.com"
port = 587
username = os.environ.get("MAIL_HOST")
password = os.environ.get("MAIL_PASSWORD")

try:
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(username, password)
    print("✅ Login successful — credentials are correct.")
    server.quit()
except smtplib.SMTPAuthenticationError:
    print("❌ Authentication failed — username or password incorrect.")
except Exception as e:
    print(f"⚠️ Error: {e}")
