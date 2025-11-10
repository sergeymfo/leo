// Конфігурація
const CONFIG = {
    bmcUsername: 'fwdr', // Ваш Buy Me a Coffee username
    basePrice: 1,        // Базова ціна "кави" на BMC ($1)
    minAmount: 1,        // Мінімальна сума в доларах
    maxAmount: 1000,     // Максимальна сума в доларах
    currency: 'USD',     // Валюта

    // Direct links до BMC Extras для кожної суми
    // Створіть extras на https://buymeacoffee.com/fwdr/shop
    extrasLinks: {
        5: null,    // Поки не створено
        10: 'https://buymeacoffee.com/fwdr/e/477543', // ✅ Створено
        25: null,   // Поки не створено
        50: null,   // Поки не створено
        100: null   // Поки не створено
    }
};

// Стан додатку
let selectedAmount = 0;
let tg = null;

// Ініціалізація
document.addEventListener('DOMContentLoaded', () => {
    initTelegramWebApp();
    initAmountButtons();
    initCustomAmount();
    initDonateButton();
    updateUI();
});

// Ініціалізація Telegram Web App
function initTelegramWebApp() {
    if (window.Telegram && window.Telegram.WebApp) {
        tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();

        // Налаштування теми
        document.body.style.backgroundColor = tg.backgroundColor || '#ffffff';

        // Налаштування головної кнопки
        tg.MainButton.setText('💝 Підтримати проект');
        tg.MainButton.onClick(handleDonate);

        console.log('Telegram Web App initialized');
    } else {
        console.log('Running in browser mode (not in Telegram)');
    }
}

// Ініціалізація кнопок з сумами
function initAmountButtons() {
    const buttons = document.querySelectorAll('.amount-button');

    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const amount = parseInt(button.dataset.amount);
            selectAmount(amount);

            // Зняти виділення з інших кнопок
            buttons.forEach(btn => btn.classList.remove('selected'));
            button.classList.add('selected');

            // Очистити custom input
            document.getElementById('customAmount').value = '';
        });
    });
}

// Ініціалізація custom amount input
function initCustomAmount() {
    const input = document.getElementById('customAmount');

    input.addEventListener('input', (e) => {
        let value = parseInt(e.target.value) || 0;

        // Обмеження значень
        if (value > CONFIG.maxAmount) {
            value = CONFIG.maxAmount;
            e.target.value = value;
        }

        selectAmount(value);

        // Зняти виділення з кнопок
        document.querySelectorAll('.amount-button').forEach(btn => {
            btn.classList.remove('selected');
        });
    });

    // Валідація при втраті фокусу
    input.addEventListener('blur', (e) => {
        let value = parseInt(e.target.value) || 0;

        if (value > 0 && value < CONFIG.minAmount) {
            value = CONFIG.minAmount;
            e.target.value = value;
            selectAmount(value);
        }
    });
}

// Ініціалізація кнопки донату
function initDonateButton() {
    const button = document.getElementById('donateButton');
    button.addEventListener('click', handleDonate);
}

// Вибір суми
function selectAmount(amount) {
    selectedAmount = amount;
    updateUI();
}

// Оновлення UI
function updateUI() {
    const selectedAmountEl = document.getElementById('selectedAmount');
    const donateButton = document.getElementById('donateButton');

    // Оновлення відображення суми
    selectedAmountEl.textContent = selectedAmount;

    // Активація/деактивація кнопки
    const isValid = selectedAmount >= CONFIG.minAmount && selectedAmount <= CONFIG.maxAmount;
    donateButton.disabled = !isValid;

    // Оновлення головної кнопки Telegram
    if (tg) {
        if (isValid) {
            tg.MainButton.show();
            tg.MainButton.setText(`💝 Підтримати ${selectedAmount} ${CONFIG.currency}`);
        } else {
            tg.MainButton.hide();
        }
    }
}

// Обробка донату
function handleDonate() {
    if (selectedAmount < CONFIG.minAmount || selectedAmount > CONFIG.maxAmount) {
        showError(`Введіть суму від ${CONFIG.minAmount} до ${CONFIG.maxAmount} ${CONFIG.currency}`);
        return;
    }

    // Генеруємо унікальний payment ID для відстеження
    const userId = tg ? tg.initDataUnsafe?.user?.id : null;
    const timestamp = Date.now();
    const paymentId = userId ? `${userId}_${timestamp}` : `guest_${timestamp}`;

    // Перевіряємо чи є direct link до extra для цієї суми
    const extraLink = CONFIG.extrasLinks[selectedAmount];

    let bmcUrl;
    if (extraLink) {
        // Використовуємо direct link до extra (сума вже встановлена в extra)
        bmcUrl = extraLink;
        console.log('Using direct extra link');
    } else {
        // Fallback: відкриваємо загальний профіль
        bmcUrl = `https://www.buymeacoffee.com/${CONFIG.bmcUsername}`;
        console.log('Extra not configured, using profile link');
    }

    console.log('Donate clicked:', {
        selectedAmount,
        currency: CONFIG.currency,
        paymentId,
        userId,
        hasExtraLink: !!extraLink,
        bmcUrl
    });

    // Відправка даних до бота (ОБОВ'ЯЗКОВО!)
    // Бот збереже pending payment в БД
    if (tg) {
        tg.sendData(JSON.stringify({
            action: 'init_payment',
            payment_id: paymentId,
            amount: selectedAmount,
            currency: CONFIG.currency,
            user_id: userId,
            timestamp: timestamp
        }));

        console.log('Payment data sent to bot');
    }

    // Показуємо користувачу payment ID (ВАЖЛИВО для webhook)
    // Користувач має вказати його в "Say something nice" полі
    if (tg && userId) {
        tg.showAlert(
            `💡 Важливо!\n\n` +
            `Після оплати в полі "Say something nice" вкажіть:\n` +
            `${paymentId}\n\n` +
            `Це потрібно для автоматичного зарахування бонусів.`
        );
    }

    // Відкриття Buy Me a Coffee
    setTimeout(() => {
        window.open(bmcUrl, '_blank');
    }, tg ? 2000 : 0); // Даємо час прочитати повідомлення

    // НЕ закриваємо Web App одразу - користувач може повернутись
}

// Показати помилку
function showError(message) {
    if (tg) {
        tg.showAlert(message);
    } else {
        alert(message);
    }
}

// Експорт для використання в інших скриптах
window.leoDonation = {
    selectAmount,
    handleDonate,
    getSelectedAmount: () => selectedAmount
};
