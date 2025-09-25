import httpx
import hashlib
import hmac
from typing import Dict, Any
from src.core.config import settings
from src.core.logging_config import get_logger


class HeleketService:
    def __init__(self):
        self.base_url = "https://api.heleket.com/v1"
        self.merchant_id = settings.HELEKET_MERCHANT_ID
        self.api_key = settings.HELEKET_API_KEY
        self.secret_key = settings.HELEKET_SECRET_KEY
        self.logger = get_logger(__name__)

    def _generate_signature(self, data: str) -> str:
        message = f"{self.merchant_id}{data}"
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

    async def create_payment(
            self,
            amount: float,
            currency: str,
            order_id: str,
            user_id: int,
            **additional_params
    ) -> Dict[str, Any]:
        try:
            signature_data = f"{amount}{currency}{order_id}"
            headers = {
                "merchant": self.merchant_id,
                "sign": self._generate_signature(signature_data),
                "Content-Type": "application/json"
            }

            payload = {
                "amount": str(amount),
                "currency": currency,
                "order_id": order_id,
                "url_callback": f"{settings.BASE_URL}/api/webhooks/heleket",
                "url_return": f"{settings.FRONTEND_URL}/payment/return",
                "url_success": f"{settings.FRONTEND_URL}/payment/success",
                "lifetime": 3600,
                **additional_params
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/payment",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )

                if response.status_code != 200:
                    self.logger.error(f"Heleket API error: {response.status_code} - {response.text}")
                    raise Exception(f"Payment creation failed: {response.text}")

                return response.json()

        except Exception as e:
            self.logger.error(f"Error creating Heleket payment: {e}")
            raise
