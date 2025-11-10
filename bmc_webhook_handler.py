"""
Buy Me a Coffee Webhook Handler для автоматичного відстеження оплат

Інструкція з налаштування:
1. Додайте цей код в ваш Telegram бот
2. Налаштуйте webhook URL в BMC Dashboard
3. Створіть таблицю pending_payments в БД
"""

from aiogram import Bot, Router
from aiogram.types import Message
from aiohttp import web
import json
import logging
from datetime import datetime, timedelta

router = Router()
logger = logging.getLogger(__name__)

# ====================
# 1. ОБРОБКА WEB APP DATA
# ====================

@router.message(lambda message: message.web_app_data)
async def handle_webapp_data(message: Message, bot: Bot):
    """
    Обробка даних з Web App (коли користувач натиснув "Підтримати")
    """
    try:
        data = json.loads(message.web_app_data.data)

        if data.get('action') == 'init_payment':
            # Зберігаємо pending payment в БД
            payment_id = data['payment_id']
            amount = data['amount']
            user_id = data['user_id']

            # Зберегти в БД (приклад)
            await db.create_pending_payment(
                payment_id=payment_id,
                user_id=user_id,
                telegram_id=message.from_user.id,
                amount=amount,
                currency=data['currency'],
                status='pending',
                created_at=datetime.now()
            )

            await message.answer(
                f"✅ Очікую оплату на суму ${amount}\n\n"
                f"🔑 Ваш Payment ID:\n"
                f"<code>{payment_id}</code>\n\n"
                f"📝 ВАЖЛИВО: При оплаті вкажіть цей ID "
                f"в полі 'Say something nice'\n\n"
                f"💡 Після оплати бонуси зарахуються автоматично!",
                parse_mode='HTML'
            )

            logger.info(f"Pending payment created: {payment_id} for user {user_id}")

    except Exception as e:
        logger.error(f"Error handling webapp data: {e}")
        await message.answer("❌ Помилка обробки даних. Спробуйте ще раз.")


# ====================
# 2. BMC WEBHOOK ENDPOINT
# ====================

async def bmc_webhook_handler(request):
    """
    Обробка webhooks від Buy Me a Coffee

    Налаштування webhook в BMC:
    1. https://buymeacoffee.com/fwdr/integrations
    2. Webhooks → Add webhook
    3. URL: https://your-domain.com/bmc-webhook
    4. Events: New supporter, New membership
    """
    try:
        data = await request.json()

        logger.info(f"BMC Webhook received: {json.dumps(data)}")

        # Дані від BMC
        supporter_name = data.get('supporter_name')
        supporter_email = data.get('supporter_email')
        support_note = data.get('support_note', '')
        support_coffees = data.get('support_coffees', 1)
        support_price = data.get('support_coffee_price', 5)
        total_amount = float(support_coffees) * float(support_price)

        logger.info(f"Payment received: ${total_amount} from {supporter_name}")

        # АВТОМАТИЧНИЙ ПОШУК: шукаємо pending payment по сумі і часу
        # Беремо всі pending за останні 30 хвилин з такою сумою
        pending = await db.find_pending_by_amount_and_time(
            amount=total_amount,
            time_window_minutes=30
        )

        if pending and pending.status == 'pending':
            # Знайдено! Оновлюємо статус
            await db.update_payment_status(
                payment_id=pending.payment_id,
                status='completed',
                completed_at=datetime.now(),
                bmc_data=data
            )

            # Зараховуємо бонуси користувачу
            bonus_amount = int(total_amount * 100)  # 1$ = 100 кредитів
            await db.add_balance(pending.telegram_id, bonus_amount)

            # Відправляємо повідомлення користувачу
            bot = request.app['bot']  # Отримуємо bot instance
            await bot.send_message(
                pending.telegram_id,
                f"🎉 <b>Оплата успішна!</b>\n\n"
                f"💰 Сума: ${total_amount}\n"
                f"⭐ Нараховано: <b>{bonus_amount}</b> кредитів\n"
                f"👤 Від: {supporter_name}\n\n"
                f"Дякуємо за підтримку! ❤️",
                parse_mode='HTML'
            )

            logger.info(f"Payment completed: {pending.payment_id}, credited {bonus_amount} credits")

            return web.Response(
                text=json.dumps({'status': 'success', 'message': 'Payment processed'}),
                status=200,
                content_type='application/json'
            )

        else:
            # Pending payment не знайдено або вже оброблено
            if not pending:
                logger.warning(f"No pending payment found for amount ${total_amount} in last 30 minutes")
            else:
                logger.warning(f"Payment already processed: {pending.payment_id}")

            return web.Response(
                text=json.dumps({'status': 'warning', 'message': 'Payment ID not found'}),
                status=200,
                content_type='application/json'
            )

    except Exception as e:
        logger.error(f"BMC webhook error: {e}", exc_info=True)
        return web.Response(
            text=json.dumps({'status': 'error', 'message': str(e)}),
            status=500,
            content_type='application/json'
        )


# ====================
# 3. SETUP WEB SERVER
# ====================

async def setup_webhook_server(bot: Bot, port: int = 8080):
    """
    Налаштування веб-сервера для webhooks
    """
    app = web.Application()
    app['bot'] = bot  # Зберігаємо bot instance

    # Додаємо route для BMC webhook
    app.router.add_post('/bmc-webhook', bmc_webhook_handler)

    # Запускаємо сервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    logger.info(f"Webhook server started on port {port}")
    logger.info(f"BMC Webhook URL: http://your-domain.com:{port}/bmc-webhook")


# ====================
# 4. DATABASE MODELS (приклад)
# ====================

class DatabaseExample:
    """
    Приклад методів для роботи з БД
    Адаптуйте під вашу БД (SQLAlchemy, MongoDB, etc.)
    """

    async def create_pending_payment(self, payment_id, user_id, telegram_id,
                                     amount, currency, status, created_at):
        """
        CREATE TABLE pending_payments (
            payment_id VARCHAR(100) PRIMARY KEY,
            user_id BIGINT,
            telegram_id BIGINT,
            amount DECIMAL(10, 2),
            currency VARCHAR(10),
            status VARCHAR(20),
            created_at TIMESTAMP,
            completed_at TIMESTAMP NULL,
            bmc_data JSON NULL
        );
        """
        # Ваша реалізація
        pass

    async def get_pending_payment(self, payment_id):
        """Отримати pending payment по ID"""
        # Ваша реалізація
        pass

    async def update_payment_status(self, payment_id, status, completed_at, bmc_data):
        """Оновити статус платежу"""
        # Ваша реалізація
        pass

    async def add_balance(self, telegram_id, amount):
        """Додати баланс користувачу"""
        # Ваша реалізація
        pass

    async def find_pending_by_amount_and_time(self, amount, time_window_minutes):
        """
        Знайти перший pending payment по сумі за останні N хвилин (FIFO)

        SELECT * FROM pending_payments
        WHERE amount = {amount}
        AND status = 'pending'
        AND created_at > NOW() - INTERVAL {time_window_minutes} MINUTE
        ORDER BY created_at ASC
        LIMIT 1;
        """
        # Ваша реалізація
        # Повертає перший (найстаріший) pending з такою сумою
        pass


# ====================
# 5. MAIN (приклад запуску)
# ====================

async def main():
    """
    Приклад інтеграції в бота
    """
    from aiogram import Dispatcher

    bot = Bot(token="YOUR_BOT_TOKEN")
    dp = Dispatcher()

    # Реєструємо роутер
    dp.include_router(router)

    # Запускаємо webhook server
    await setup_webhook_server(bot, port=8080)

    # Запускаємо бота
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
