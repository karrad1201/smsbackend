import requests
import json
import hashlib
import base64
import os
import dotenv

dotenv.load_dotenv()

def make_test_payment(
    amount="15",
    currency="USD",
    order_id="1",
    merchant_id: str | None = None,
    secret_key: str | None = None,
):
    merchant_id = merchant_id or os.getenv("HELEKET_MERCHANT_UUID")
    secret_key = secret_key or os.getenv("HELEKET_SECRET_KEY")
    if not merchant_id or not secret_key:
        print("⚠️ Установите переменные окружения HELEKET_MERCHANT_UUID и HELEKET_SECRET_KEY или передайте параметры явно.")
        return None

    url = "https://api.heleket.com/v1/payment"
    payment_data = {
        "amount": amount,
        "currency": currency,
        "order_id": order_id
    }

    body_json = json.dumps(payment_data, separators=(',', ':'), ensure_ascii=False)
    base64_data = base64.b64encode(body_json.encode('utf-8')).decode('utf-8')
    signature = hashlib.md5((base64_data + secret_key).encode('utf-8')).hexdigest()

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json;charset=UTF-8',
        'Content-Length': str(len(body_json.encode('utf-8'))),
        'merchant': merchant_id,
        'sign': signature
    }

    try:
        response = requests.post(url, headers=headers, data=body_json.encode('utf-8'))
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Request Headers: {headers}")
        print(f"Request Body: {body_json}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при выполнении запроса: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Text: {e.response.text}")
        return None


def create_test_payment_link(amount="15", currency="USD", order_id=None, secret_key=None, merchant_id=None):
    import time

    if order_id is None:
        order_id = f"test_order_{int(time.time())}"

    if merchant_id is None:
        merchant_id = os.getenv("HELEKET_MERCHANT_UUID")
    if secret_key is None:
        secret_key = os.getenv("HELEKET_SECRET_KEY")
    
    print(f"🔧 Создаем тестовую ссылку на платежку...")
    print(f"   Сумма: {amount} {currency}")
    print(f"   Заказ: {order_id}")
    print()
    
    result = make_test_payment(
        amount=amount,
        currency=currency,
        order_id=order_id,
        merchant_id=merchant_id,
        secret_key=secret_key
    )
    
    if result:
        print("✅ Платежная ссылка успешно создана!")
        payment_url = result.get("result", {}).get("url")
        if payment_url:
            print(f"🔗 Ссылка на платежку: {payment_url}")
            return {
                'success': True,
                'payment_url': payment_url,
                'order_id': order_id,
                'amount': amount,
                'currency': currency,
                'full_response': result
            }
        else:
            print("⚠️ Ссылка на платежку не найдена в ответе")
            print(f"📋 Полный ответ API: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return {
                'success': False,
                'error': 'Payment URL not found in response',
                'full_response': result
            }
    else:
        print("❌ Ошибка при создании платежной ссылки")
        return {
            'success': False,
            'error': 'Failed to create payment link'
        }


if __name__ == "__main__":
    print("=== Тестирование создания платежной ссылки ===")
    print()
    
    result = create_test_payment_link()
    
    if result and result.get('success'):
        print(f"✅ Успешно! Ссылка: {result.get('payment_url')}")
    else:
        print(f"❌ Ошибка: {result.get('error') if result else 'Нет ответа'}")