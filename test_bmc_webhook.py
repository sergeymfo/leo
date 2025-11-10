#!/usr/bin/env python3
"""
Тестовий webhook handler для Buy Me a Coffee
Використовується для перевірки webhooks перед інтеграцією в основний бот
"""

from aiohttp import web
import json
import logging
from datetime import datetime

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def bmc_webhook_handler(request):
    """
    Тестовий обробник webhooks від Buy Me a Coffee
    Просто виводить отримані дані в консоль
    """
    try:
        # Отримуємо дані
        data = await request.json()

        # Виводимо повний payload
        print("\n" + "=" * 70)
        print("🎉 WEBHOOK ОТРИМАНО!")
        print(f"⏰ Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print("\n📦 Повний JSON payload:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("\n" + "=" * 70)

        # Розбираємо дані (офіційний формат BMC)
        response = data.get('response', {})

        if response:
            print("\n✅ Розібрані дані:")
            print(f"   👤 Ім'я: {response.get('supporter_name', 'N/A')}")
            print(f"   📧 Email: {response.get('supporter_email', 'N/A')}")
            print(f"   💰 Сума: ${response.get('total_amount', '0')}")
            print(f"   💬 Повідомлення: {response.get('support_note', '(немає)')}")
            print(f"   📅 Дата: {response.get('support_created_on', 'N/A')}")
            print(f"   ☕ Кількість: {response.get('number_of_coffees', 'N/A')}")
        else:
            print("\n⚠️ Дані не містять 'response' об'єкт")

        print("\n" + "=" * 70 + "\n")

        # Відповідь BMC (обов'язково 200 OK!)
        return web.Response(
            text=json.dumps({'status': 'success', 'message': 'Webhook received'}),
            status=200,
            content_type='application/json'
        )

    except json.JSONDecodeError as e:
        logger.error(f"❌ Помилка парсингу JSON: {e}")
        return web.Response(
            text=json.dumps({'status': 'error', 'message': 'Invalid JSON'}),
            status=400,
            content_type='application/json'
        )

    except Exception as e:
        logger.error(f"❌ Помилка обробки webhook: {e}", exc_info=True)
        return web.Response(
            text=json.dumps({'status': 'error', 'message': str(e)}),
            status=500,
            content_type='application/json'
        )


async def health_check(request):
    """Endpoint для перевірки що сервер працює"""
    return web.Response(
        text=json.dumps({
            'status': 'ok',
            'message': 'BMC Webhook Test Server is running',
            'time': datetime.now().isoformat()
        }),
        status=200,
        content_type='application/json'
    )


def create_app():
    """Створення aiohttp app"""
    app = web.Application()

    # Роути
    app.router.add_post('/bmc-webhook', bmc_webhook_handler)
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)

    return app


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 BMC WEBHOOK TEST SERVER")
    print("=" * 70)
    print("\n📍 Endpoints:")
    print("   POST /bmc-webhook  - BMC webhook handler")
    print("   GET  /health       - Health check")
    print("   GET  /             - Health check")
    print("\n🔧 Port: 8080")
    print("🌐 Host: 0.0.0.0 (всі інтерфейси)")
    print("\n💡 Для використання з BMC:")
    print("   1. Запустіть ngrok: ngrok http 8080")
    print("   2. Скопіюйте HTTPS URL з ngrok")
    print("   3. Додайте /bmc-webhook в кінці URL")
    print("   4. Вставте в BMC webhook settings")
    print("\n" + "=" * 70)
    print("⏳ Запуск сервера...\n")

    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080)
