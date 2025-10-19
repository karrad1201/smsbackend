# debug_and_fix_prices.py
import requests
import json
import time
import subprocess


class PriceDebugger:
    def __init__(self, jwt_token):
        self.base_url = "http://localhost:8000"
        self.headers = {"Authorization": f"Bearer {jwt_token}"}

    def run_sql(self, sql):
        """Выполнить SQL команду"""
        cmd = f'docker-compose exec db psql -U dbadmin -d sms_api_dev -c "{sql}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result

    def check_current_data(self):
        """Проверить текущие данные в БД"""
        print("🔍 ПРОВЕРЯЕМ ДАННЫЕ В БАЗЕ:")
        print("=" * 60)

        # Проверяем сервисы
        print("\n📱 СЕРВИСЫ:")
        result = self.run_sql("SELECT code, name, is_active FROM service_reference WHERE code IN ('tg', 'wa', 'vk');")
        print(result.stdout)

        # Проверяем страны
        print("\n🌍 СТРАНЫ:")
        result = self.run_sql("SELECT code, name_ru, is_active FROM country_reference WHERE code = 'ru';")
        print(result.stdout)

        # Проверяем провайдеров
        print("\n🏢 ПРОВАЙДЕРЫ:")
        result = self.run_sql("SELECT id, name, is_active FROM providers WHERE name = 'sms-room';")
        print(result.stdout)

        # Проверяем маршруты
        print("\n🛣️ МАРШРУТЫ:")
        result = self.run_sql("""
        SELECT pr.country_code, pr.service_code, pr.provider_country_code, pr.provider_service_code, 
               pr.cost_price, pr.client_price, pr.available_count, pr.is_active,
               p.name as provider_name
        FROM provider_routes pr
        JOIN providers p ON pr.provider_id = p.id
        WHERE pr.service_code IN ('tg', 'wa', 'vk') AND pr.country_code = 'ru';
        """)
        print(result.stdout)

    def fix_prices_correctly(self):
        """Исправить цены правильно"""
        print("\n🔧 ИСПРАВЛЯЕМ ДАННЫЕ ЦЕН:")
        print("=" * 60)

        sql_commands = [
            # Удаляем старые данные чтобы избежать конфликтов
            "DELETE FROM provider_routes WHERE service_code IN ('tg', 'wa', 'vk') AND country_code = 'ru';",
            "DELETE FROM service_reference WHERE code IN ('tg', 'wa', 'vk');",
            "DELETE FROM country_reference WHERE code = 'ru';",
            "DELETE FROM providers WHERE name = 'sms-room';",

            # Добавляем провайдера с правильными настройками
            """
            INSERT INTO providers (name, adapter_class, config, is_active, display_name, api_url, api_key, adapter_type, mapping_type) 
            VALUES ('sms-room', 'SMSRoomAdapter', '{"api_key": "test_key"}', true, 'SMS Room', 'https://sms-rooms.com/stubs/handler_api.php', 'test_multi_provider_key_12345', 'smsactivate', 'smsactivate_type');
            """,

            # Добавляем сервисы
            """
            INSERT INTO service_reference (code, name, category, is_popular, is_active, sort_order) 
            VALUES 
            ('tg', 'Telegram', 'social', true, true, 1),
            ('wa', 'WhatsApp', 'social', true, true, 2),
            ('vk', 'VKontakte', 'social', true, true, 3)
            ON CONFLICT (code) DO UPDATE SET 
                name = EXCLUDED.name,
                is_active = EXCLUDED.is_active;
            """,

            # Добавляем страну
            """
            INSERT INTO country_reference (code, name_ru, name_en, is_active, iso_code, is_popular, sort_order) 
            VALUES ('ru', 'Россия', 'Russia', true, 'RU', true, 1)
            ON CONFLICT (code) DO UPDATE SET 
                name_ru = EXCLUDED.name_ru,
                is_active = EXCLUDED.is_active;
            """,

            # Добавляем маршруты с правильными provider_service_code
            """
            INSERT INTO provider_routes (provider_id, country_code, service_code, provider_country_code, provider_service_code, cost_price, client_price, available_count, is_active, priority)
            SELECT 
                p.id, 'ru', 'tg', '0', 'tg', 5.0, 10.0, 100, true, 1
            FROM providers p 
            WHERE p.name = 'sms-room';
            """,

            """
            INSERT INTO provider_routes (provider_id, country_code, service_code, provider_country_code, provider_service_code, cost_price, client_price, available_count, is_active, priority)
            SELECT 
                p.id, 'ru', 'wa', '0', 'wa', 6.0, 12.0, 50, true, 1
            FROM providers p 
            WHERE p.name = 'sms-room';
            """,

            """
            INSERT INTO provider_routes (provider_id, country_code, service_code, provider_country_code, provider_service_code, cost_price, client_price, available_count, is_active, priority)
            SELECT 
                p.id, 'ru', 'vk', '0', 'vk', 4.0, 8.0, 80, true, 1
            FROM providers p 
            WHERE p.name = 'sms-room';
            """
        ]

        for i, sql in enumerate(sql_commands, 1):
            print(f"Выполняем команду {i}/6...")
            result = self.run_sql(sql)
            if result.returncode != 0:
                print(f"❌ Ошибка в команде {i}: {result.stderr}")
                return False
            time.sleep(0.5)

        print("✅ Данные успешно обновлены!")
        return True

    def test_price_repository(self):
        """Протестировать репозиторий цен напрямую"""
        print("\n🧪 ТЕСТИРУЕМ РЕПОЗИТОРИЙ ЦЕН:")
        print("=" * 60)

        test_cases = [
            ("tg", "ru"),
            ("wa", "ru"),
            ("vk", "ru")
        ]

        for service, country in test_cases:
            response = requests.post(
                f"{self.base_url}/orders/validate",
                headers=self.headers,
                json={"service": service, "country_code": country}
            )

            if response.status_code == 200:
                result = response.json()
                print(f"Сервис: {service}, Страна: {country}")
                print(f"  valid: {result.get('valid')}")
                print(f"  available: {result.get('available')}")
                print(f"  price: {result.get('price')}")
                print(f"  service_name: {result.get('service_name')}")
                print(f"  country_name: {result.get('country_name')}")
                print()
            else:
                print(f"❌ Ошибка для {service}/{country}: {response.status_code}")

    def test_with_different_services(self):
        """Тестируем с разными сервисами которые точно есть"""
        print("\n🎯 ТЕСТИРУЕМ С РАЗНЫМИ СЕРВИСАМИ:")
        print("=" * 60)

        # Популярные сервисы которые обычно есть
        services_to_try = [
            "tg", "wa", "vk", "ok", "fb", "ig", "go", "vi", "ym", "mb", "mm", "uk"
        ]

        working_services = []

        for service in services_to_try:
            response = requests.post(
                f"{self.base_url}/orders/validate",
                headers=self.headers,
                json={"service": service, "country_code": "ru"}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('available'):
                    working_services.append((service, result))
                    print(f"✅ {service}: ДОСТУПЕН - {result.get('price')} руб.")
                else:
                    print(f"❌ {service}: недоступен")
            else:
                print(f"⚠️ {service}: ошибка {response.status_code}")

            time.sleep(0.5)  # Чтобы не перегружать API

        return working_services

    def run_debug(self):
        """Запускаем отладку"""
        print("🐛 ЗАПУСК ОТЛАДКИ СИСТЕМЫ ЦЕН")
        print("=" * 60)

        # 1. Проверяем текущие данные
        self.check_current_data()
        time.sleep(2)

        # 2. Исправляем данные
        if self.fix_prices_correctly():
            time.sleep(2)

            # 3. Проверяем после исправления
            print("\n" + "=" * 60)
            self.check_current_data()
            time.sleep(2)

            # 4. Тестируем репозиторий
            print("\n" + "=" * 60)
            self.test_price_repository()
            time.sleep(2)

            # 5. Ищем рабочие сервисы
            print("\n" + "=" * 60)
            working_services = self.test_with_different_services()

            if working_services:
                print(f"\n🎉 НАЙДЕНО РАБОЧИХ СЕРВИСОВ: {len(working_services)}")
                for service, data in working_services:
                    print(f"   📱 {service}: {data.get('price')} руб. - {data.get('service_name')}")
                return working_services
            else:
                print("\n😞 НЕТ РАБОЧИХ СЕРВИСОВ")
                return []

        return []


def main():
    JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTc2MDYzMjg2NCwiaWF0IjoxNzYwNjI5MjY0fQ.LupYBKM329xuMzQwJGnTPDMeq-FJ3lCVT8_18DV93qk"

    debugger = PriceDebugger(JWT_TOKEN)
    working_services = debugger.run_debug()

    if working_services:
        print(f"\n🚀 ДЛЯ ТЕСТИРОВАНИЯ ИСПОЛЬЗУЙТЕ:")
        for service, data in working_services[:3]:  # Первые 3 рабочих
            print(f"   Сервис: {service}, Страна: ru")


if __name__ == "__main__":
    main()