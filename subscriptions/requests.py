import os
import requests
from dotenv import load_dotenv

load_dotenv()

paystack_key = os.getenv('PAYSTACK_TEST_SECRET_KEY')

headers = {
                "Authorization": f"Bearer {paystack_key}",
                "Content-Type": "application/json"
            }

base_url = "https://api.paystack.co/"

def send_paystack_request(method, url, payload=None):
        # print(f'{base_url}{url}')
        response = requests.request(method, f'{base_url}{url}', json=payload, headers=headers)
        return response
    
def create_plan(payload):
    response = send_paystack_request("POST", "plan", payload)
    response_data = response.json()
    
    print(response_data)
    
    if response.status_code == 201 and response_data.get("status"):
        return response_data["data"]["plan_code"]
    
    raise Exception(response_data.get("message", "Failed to create Paystack plan"))