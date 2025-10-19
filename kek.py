# fix_and_test_orders.py
import requests
import json
import time
import subprocess


class OrderSystemTester:
    def __init__(self, jwt_token):
        self.base_url = "http://localhost:8000"
        self.headers = {"Authorization": f"Bearer {jwt_token}"}
        self.user_id = 6  # Из логов видно, что user_id = 6

    def run_sql(self, sql):
        """Выполнить SQL команду"""
        cmd = f'docker-compose exec db psql -U dbadmin -d sms_api_dev -c "{sql}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result

    def fix_user_api_key(self):
        """Добавляем API ключ пользователю"""
        print("🔑 Исправляем API ключ пользователя...")

        sql = f"""
        UPDATE users 
        SET api_key = 'test_multi_provider_key_12345' 
        WHERE id = {self.user_id};
        """

        result = self.run_sql(sql)
        if result.returncode == 0:
            print("✅ API ключ добавлен пользователю")
            return True
        else:
            print(f"❌ Ошибка: {result.stderr}")
            return False

    def fix_prices_data(self):
        """Добавляем тестовые данные для цен"""
        print("💰 Добавляем тестовые цены...")

        # Сначала добавляем сервис и страну если их нет
        sql_commands = [
            # Добавляем сервис Telegram
            """
            INSERT INTO service_reference (code, name, category, is_popular, is_active) 
            VALUES ('tg', 'Telegram', 'social', true, true)
            ON CONFLICT (code) DO NOTHING;
            """,

            # Добавляем страну Россия
            """
            INSERT INTO country_reference (code, name_ru, name_en, is_active, iso_code) 
            VALUES ('ru', 'Россия', 'Russia', true, 'RU')
            ON CONFLICT (code) DO NOTHING;
            """,

            # Добавляем провайдера
            """
            INSERT INTO providers (name, adapter_class, config, is_active, display_name, api_url, api_key, adapter_type) 
            VALUES ('sms-room', 'SMSRoomAdapter', '{}', true, 'SMS Room', 'https://sms-rooms.com/stubs/handler_api.php', 'test_key', 'smsactivate')
            ON CONFLICT (name) DO NOTHING;
            """,

            # Добавляем маршрут для Telegram/Россия
            """
            INSERT INTO provider_routes (provider_id, country_code, service_code, provider_country_code, provider_service_code, cost_price, client_price, available_count, is_active)
            SELECT 
                p.id, 'ru', 'tg', '0', 'tg', 5.0, 10.0, 100, true
            FROM providers p 
            WHERE p.name = 'sms-room'
            ON CONFLICT DO NOTHING;
            """
        ]

        for sql in sql_commands:
            result = self.run_sql(sql)
            if result.returncode != 0:
                print(f"❌ Ошибка выполнения SQL: {result.stderr}")
                return False

        print("✅ Тестовые данные цен добавлены")
        return True

    def test_validate_order(self):
        """Тестируем валидацию с правильными данными"""
        print("\n🔍 Тестируем валидацию заказа...")

        # Пробуем разные сервисы и страны
        test_cases = [
            {"service": "tg", "country_code": "ru"},
            {"service": "wa", "country_code": "ru"},  # WhatsApp
            {"service": "vk", "country_code": "ru"},  # VK
        ]

        for test_data in test_cases:
            response = requests.post(
                f"{self.base_url}/orders/validate",
                headers=self.headers,
                json=test_data
            )

            print(f"Сервис: {test_data['service']}, Страна: {test_data['country_code']}")
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Результат: valid={result.get('valid')}, available={result.get('available')}")
                if result.get('valid'):
                    return test_data  # Возвращаем рабочий вариант
            else:
                print(f"  ❌ Ошибка: {response.status_code}")

        return None

    def test_create_order(self, order_data):
        """Тестируем создание заказа"""
        print(f"\n🆕 Создаем заказ: {order_data}...")

        response = requests.post(
            f"{self.base_url}/orders/create",
            headers=self.headers,
            json=order_data
        )

        if response.status_code == 200:
            result = response.json()
            order_id = result.get('id')
            print(f"✅ Заказ создан! ID: {order_id}")
            print(f"   📱 Номер: {result.get('phone_number')}")
            print(f"   📊 Статус: {result.get('status')}")
            print(f"   💰 Цена: {result.get('price')}")
            return order_id
        else:
            print(f"❌ Ошибка создания: {response.status_code}")
            print(f"   Текст: {response.text}")
            return None

    def test_poll_order_status(self, order_id):
        """Тестируем опрос статуса"""
        print(f"\n🔄 Опрашиваем статус заказа {order_id}...")

        response = requests.get(
            f"{self.base_url}/orders/{order_id}/poll",
            headers=self.headers
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Статус получен:")
            print(f"   📊 Статус: {result.get('status')}")
            print(f"   🔢 Код: {result.get('code')}")
            print(f"   📱 Номер: {result.get('phone_number')}")
            return True
        else:
            print(f"❌ Ошибка опроса: {response.status_code}")
            return False

    def test_get_orders_list(self):
        """Тестируем получение списка заказов"""
        print("\n📋 Получаем список заказов...")

        response = requests.get(
            f"{self.base_url}/orders/my",
            headers=self.headers
        )

        if response.status_code == 200:
            result = response.json()
            orders = result.get('orders', [])
            print(f"✅ Заказов найдено: {len(orders)}")

            for order in orders[:3]:  # Показываем первые 3
                print(f"   📦 {order.get('id')}: {order.get('service')} - {order.get('status')}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return False

    def test_dashboard_stats(self):
        """Тестируем статистику dashboard"""
        print("\n📊 Получаем статистику dashboard...")

        response = requests.get(
            f"{self.base_url}/orders/dashboard/stats",
            headers=self.headers
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Статистика получена:")
            print(f"   📈 Всего заказов: {result.get('total_orders')}")
            print(f"   ⚡ Активных: {result.get('active_orders')}")
            print(f"   💰 Потрачено: {result.get('total_spent')}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   Текст: {response.text}")
            return False

    def test_cancel_order(self, order_id):
        """Тестируем отмену заказа"""
        print(f"\n🚫 Отменяем заказ {order_id}...")

        response = requests.post(
            f"{self.base_url}/orders/{order_id}/cancel",
            headers=self.headers
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Заказ отменен: {result.get('message')}")
            return True
        else:
            print(f"❌ Ошибка отмены: {response.status_code}")
            return False

    def run_complete_test(self):
        """Запускаем полный тест"""
        print("🚀 ЗАПУСК ПОЛНОГО ТЕСТИРОВАНИЯ СИСТЕМЫ ЗАКАЗОВ")
        print("=" * 60)

        # 1. Исправляем данные в БД
        print("\n1. ПОДГОТОВКА ДАННЫХ:")
        self.fix_user_api_key()
        time.sleep(1)
        self.fix_prices_data()
        time.sleep(2)

        # 2. Тестируем валидацию
        print("\n2. ТЕСТИРОВАНИЕ ВАЛИДАЦИИ:")
        working_data = self.test_validate_order()
        time.sleep(2)

        if not working_data:
            print("❌ Нет рабочих сервисов для тестирования")
            return

        # 3. Тестируем создание заказа
        print("\n3. ТЕСТИРОВАНИЕ СОЗДАНИЯ ЗАКАЗА:")
        order_id = self.test_create_order(working_data)
        time.sleep(2)

        if not order_id:
            print("❌ Не удалось создать заказ")
            return

        # 4. Тестируем опрос статуса
        print("\n4. ТЕСТИРОВАНИЕ ОПРОСА СТАТУСА:")
        self.test_poll_order_status(order_id)
        time.sleep(2)

        # 5. Тестируем список заказов
        print("\n5. ТЕСТИРОВАНИЕ СПИСКА ЗАКАЗОВ:")
        self.test_get_orders_list()
        time.sleep(2)

        # 6. Тестируем статистику
        print("\n6. ТЕСТИРОВАНИЕ СТАТИСТИКИ:")
        self.test_dashboard_stats()
        time.sleep(2)

        # 7. Тестируем отмену заказа
        print("\n7. ТЕСТИРОВАНИЕ ОТМЕНЫ ЗАКАЗА:")
        self.test_cancel_order(order_id)

        print("\n" + "=" * 60)
        print("🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")


def main():
    JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTc2MDYzMjg2NCwiaWF0IjoxNzYwNjI5MjY0fQ.LupYBKM329xuMzQwJGnTPDMeq-FJ3lCVT8_18DV93qk"

    tester = OrderSystemTester(JWT_TOKEN)
    tester.run_complete_test()


if __name__ == "__main__":
    main()