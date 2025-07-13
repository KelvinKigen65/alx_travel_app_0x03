import requests
from django.conf import settings

class ChapaService:
    @staticmethod
    def initiate_payment(amount, email, tx_ref, first_name, last_name):
        url = settings.CHAPA_API_URL
        headers = {
            'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        payload = {
            'amount': str(amount),
            'currency': 'ETB',
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'tx_ref': tx_ref,
            'callback_url': f"{settings.BACKEND_URL}/api/payments/webhook/",
            'return_url': f"{settings.FRONTEND_URL}/payment-success/",
        }
        response = requests.post(url, headers=headers, json=payload)
        return response.json()