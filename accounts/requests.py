import os
import requests
from dotenv import load_dotenv

load_dotenv()

korapay_key = os.getenv('KORAPAY_LIVE_SECRET_KEY')

headers = {
                "Authorization": f"Bearer {korapay_key}",
                "Content-Type": "application/json"
            }

url = "https://api.korapay.com/merchant/api/v1/identities/ng/nin"

def verify_nin_request(nin):
        payload = {
            "id": nin,
            "verification_consent": True
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            
        except Exception as e:
            raise Exception("Unable to reach verification service") from e
            
        # print("Kora Response:", data)

        if response.ok and data.get("status"):
            return data["data"]["reference"]

        raise Exception(data.get("message", "NIN verification failed"))
        