// Конфігурація
const CONFIG = {
    bmcUsername: 'fwdr', // Ваш Buy Me a Coffee username
    basePrice: 1,        // Базова ціна "кави" на BMC ($1)
    minAmount: 1,        // Мінімальна сума в доларах
    maxAmount: 1000,     // Максимальна сума в доларах
    currency: 'USD'      // Валюта
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

    // Розрахунок кількості "кав" для Buy Me a Coffee
    // BMC працює з цілими числами "кав", де 1 кава = $1
    // Передаємо суму напряму як кількість кав
    const coffeeCount = Math.ceil(selectedAmount / CONFIG.basePrice);

    // URL для Buy Me a Coffee
    const bmcUrl = `https://www.buymeacoffee.com/${CONFIG.bmcUsername}?amount=${coffeeCount}`;

    console.log('Donate clicked:', {
        selectedAmount,
        currency: CONFIG.currency,
        coffeeCount,
        bmcUrl
    });

    // Відправка даних до бота (якщо потрібно)
    if (tg) {
        tg.sendData(JSON.stringify({
            amount: selectedAmount,
            currency: CONFIG.currency,
            coffeeCount: coffeeCount
        }));
    }

    // Відкриття Buy Me a Coffee
    window.open(bmcUrl, '_blank');

    // Закриття Web App після невеликої затримки
    setTimeout(() => {
        if (tg) {
            tg.close();
        }
    }, 1000);
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
