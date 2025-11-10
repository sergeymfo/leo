# 🔄 Автоматичне відстеження оплат BMC

## Як це працює:

1. **Користувач обирає суму** в Web App
2. **Web App відправляє дані** боту (payment_id, user_id, amount)
3. **Бот зберігає** pending payment в БД
4. **Користувач оплачує** на Buy Me a Coffee і вказує payment_id в note
5. **BMC відправляє webhook** на ваш сервер
6. **Webhook handler** знаходить pending payment по ID
7. **Автоматично зараховує** бонуси користувачу

---

## 📋 Крок 1: Створити таблицю в БД

```sql
CREATE TABLE pending_payments (
    payment_id VARCHAR(100) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    telegram_id BIGINT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    bmc_data JSON NULL,
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

---

## 🤖 Крок 2: Додати код в бот

1. **Скопіюйте** `bmc_webhook_handler.py` в ваш проект
2. **Імпортуйте** в main файл:

```python
from bmc_webhook_handler import router, setup_webhook_server

# В main функції
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Додати router для обробки Web App даних
    dp.include_router(router)

    # Запустити webhook server
    await setup_webhook_server(bot, port=8080)

    # Запустити бота
    await dp.start_polling(bot)
```

3. **Реалізуйте** методи БД (в `bmc_webhook_handler.py` є приклади)

---

## 🌐 Крок 3: Налаштувати сервер

### Варіант A: Локальний сервер + ngrok (для тесту)

```bash
# 1. Запустити бота (він запустить веб-сервер на порту 8080)
python bot.py

# 2. В іншому терміналі запустити ngrok
ngrok http 8080

# 3. Скопіювати HTTPS URL (наприклад: https://abcd1234.ngrok.io)
```

### Варіант B: Production сервер

```bash
# На вашому сервері
# 1. Налаштувати nginx як reverse proxy
# 2. Налаштувати SSL (Let's Encrypt)
# 3. Направити /bmc-webhook на порт 8080
```

Приклад nginx config:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /bmc-webhook {
        proxy_pass http://localhost:8080/bmc-webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## ☕ Крок 4: Налаштувати BMC Webhook

1. Відкрийте: **https://buymeacoffee.com/fwdr/integrations**

2. Знайдіть розділ **Webhooks**

3. Натисніть **Add Webhook**

4. Заповніть:
   - **URL**: `https://your-domain.com/bmc-webhook` (або ngrok URL)
   - **Events**:
     - ✅ New supporter
     - ✅ New membership
     - ✅ Extra purchase

5. Натисніть **Save**

6. **Протестуйте webhook**: BMC має кнопку "Test webhook"

---

## 🧪 Крок 5: Тестування

### Тест 1: Перевірка Web App

1. Відкрийте Web App в боті
2. Виберіть суму $10
3. Натисніть "Підтримати"
4. Має з'явитись alert з payment_id
5. Перевірте БД - має бути запис в `pending_payments`

### Тест 2: Перевірка webhook

1. Зробіть тестовий донат на BMC
2. В полі "Say something nice" вкажіть payment_id
3. Webhook має прийти протягом 1-2 хвилин
4. Перевірте логи бота
5. Перевірте чи зарахувались бонуси

### Перевірка логів:

```bash
# Дивитись логи бота
tail -f bot.log

# Має бути:
# INFO: Pending payment created: 123456_1699999999 for user 123456
# INFO: BMC Webhook received: {...}
# INFO: Looking for payment_id: 123456_1699999999
# INFO: Payment completed: 123456_1699999999, credited 1000 credits
```

---

## 🔧 Troubleshooting

### Webhook не приходить:

1. **Перевірте URL**: має бути HTTPS (не HTTP)
2. **Перевірте firewall**: порт має бути відкритий
3. **Перевірте логи nginx**: чи доходять запити
4. **Тест webhook**: використайте кнопку в BMC Dashboard

### Payment ID не знаходиться:

1. **Перевірте note**: користувач має вказати точний ID
2. **Fallback**: якщо ID не вказаний, шукаємо по сумі+часу
3. **Логи**: дивіться що приходить в webhook

### Бонуси не зараховуються:

1. **Перевірте БД**: чи є запис pending payment
2. **Перевірте статус**: має бути 'pending', не 'completed'
3. **Перевірте метод**: `db.add_balance()` працює коректно

---

## 📊 Моніторинг

### Корисні SQL запити:

```sql
-- Всі pending платежі
SELECT * FROM pending_payments WHERE status = 'pending';

-- Платежі за останню годину
SELECT * FROM pending_payments
WHERE created_at > NOW() - INTERVAL 1 HOUR;

-- Успішні платежі за сьогодні
SELECT COUNT(*), SUM(amount) FROM pending_payments
WHERE status = 'completed'
AND DATE(completed_at) = CURDATE();

-- Платежі які не завершились за 24 години
SELECT * FROM pending_payments
WHERE status = 'pending'
AND created_at < NOW() - INTERVAL 24 HOUR;
```

---

## 🎯 Best Practices

1. **Очищати старі pending**: видаляти pending > 24 години
2. **Логувати все**: кожен webhook, кожен payment
3. **Fallback**: якщо payment_id не вказаний, шукати по сумі
4. **Retry логіка**: якщо webhook failed, BMC може повторити
5. **Deduplicate**: перевіряти чи платіж вже оброблений

---

## ✅ Checklist

- [ ] Створена таблиця `pending_payments`
- [ ] Додано `bmc_webhook_handler.py` в проект
- [ ] Реалізовані методи БД
- [ ] Налаштований веб-сервер
- [ ] Налаштований BMC webhook
- [ ] Протестовано весь flow
- [ ] Налаштований моніторинг
- [ ] Додано логування

---

## 📞 Підтримка

Якщо виникли проблеми:
1. Перевірте логи бота
2. Перевірте БД
3. Протестуйте webhook вручну
4. Перегляньте цю інструкцію знову

**Успіхів! 🚀**
