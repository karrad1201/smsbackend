import httpx
import hashlib
import hmac
import base64
import json
from typing import Dict, Any
from src.core.config import settings
from src.core.logging_config import get_logger


class HeleketService:
    def __init__(self):
        self.base_url = "https://api.heleket.com/v1"
        self.merchant_id = settings.HELEKET_MERCHANT_ID
        self.secret_key = settings.HELEKET_SECRET_KEY
        self.logger = get_logger(__name__)

    def _generate_signature_php_style(self, data: dict) -> str:
        # Используем точную сериализацию как в PHP
        json_data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

        base64_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
        string_to_sign = base64_data + self.secret_key
        signature = hashlib.md5(string_to_sign.encode('utf-8')).hexdigest()

        self.logger.debug(f"JSON data: {json_data}")
        self.logger.debug(f"Base64 data: {base64_data}")
        self.logger.debug(f"String to sign: {string_to_sign}")
        self.logger.debug(f"Signature: {signature}")

        return signature

    def verify_webhook_signature(self, webhook_data: dict, signature: str) -> bool:
        try:
            # Логируем что пришло для верификации
            self.logger.info(f"Verifying signature for data: {webhook_data}")
            self.logger.info(f"Signature to verify: {signature}")

            expected_signature = self._generate_signature_php_style(webhook_data)
            is_valid = signature.lower() == expected_signature.lower()

            self.logger.info(f"Webhook signature verification result: {is_valid}")
            self.logger.info(f"Expected: {expected_signature}")
            self.logger.info(f"Received: {signature}")

            return is_valid

        except Exception as e:
            self.logger.error(f"Error verifying webhook signature: {e}")
            return False

    async def create_balance_topup(
            self,
            amount: float,
            currency: str,
            order_id: str,
            user_id: int,
            **additional_params
    ) -> Dict[str, Any]:
        """
        Создает платеж для пополнения баланса пользователя
        """
        try:
            payload = {
                "amount": str(f"{amount:.2f}"),
                "currency": currency,
                "order_id": order_id,
                "url_callback": f"http://bluebird.smartelex.org/webhook/heleket",
                "to_currency": "USDT",
            }

            if additional_params:
                payload.update(additional_params)

                # Детальное логирование для отладки
            self.logger.info(f"Creating Heleket payment with payload: {payload}")
            self.logger.debug(f"Heleket payment payload: {payload}")

            signature = self._generate_signature_php_style(payload)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json;charset=UTF-8",
                "merchant": self.merchant_id,
                "sign": signature
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
                    raise Exception(f"Balance topup creation failed: {response.text}")

                response_data = response.json()
                self.logger.info(f"Heleket API response: {response_data}")
                return response_data

        except Exception as e:
            self.logger.error(f"Error creating Heleket balance topup: {e}")
            raise

    async def create_payment(
            self,
            amount: float,
            currency: str,
            order_id: str,
            user_id: int,
            **additional_params
    ) -> Dict[str, Any]:
        """
        Deprecated: Используйте create_balance_topup для пополнения баланса
        """
        return await self.create_balance_topup(amount, currency, order_id, user_id, **additional_params)