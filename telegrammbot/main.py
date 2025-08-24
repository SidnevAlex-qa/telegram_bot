import requests
import matplotlib.pyplot as plt
import io
import datetime
from datetime import timedelta
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = "8379655504:AAHxYcV90_w-JNP6n0lH_w_NVyGVnf4hjr4"

# Источники данных о курсах валют
CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
EXCHANGERATE_API_URL = "8379655504:AAHxYcV90_w-JNP6n0lH_w_NVyGVnf4hjr4"
BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price"



# Клавиатура с основными командами
keyboard = [
    ['💰 Курсы валют', '📊 Графики'],
    ['🔄 Конвертер', 'ℹ️ Помощь']
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Список популярных валют
POPULAR_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'CHF', 'CAD', 'AUD', 'SGD', 'HKD', 'TRY']

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот с курсами валют.\n"
        "Я могу показать актуальные курсы, построить графики и конвертировать валюты.\n"
        "Выберите опцию:",
        reply_markup=reply_markup
    )

async def get_rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем данные от ЦБ РФ
        response = requests.get(CBR_API_URL)
        data = response.json()
        
        # Формируем сообщение с курсами
        message = "💰 Курсы валют ЦБ РФ:\n\n"
        
        for currency in POPULAR_CURRENCIES:
            if currency in data['Valute']:
                rate = data['Valute'][currency]['Value']
                nominal = data['Valute'][currency]['Nominal']
                if nominal > 1:
                    message += f"• {currency}: {rate:.2f} ₽ (за {nominal} ед.)\n"
                else:
                    message += f"• {currency}: {rate:.2f} ₽\n"
        
        # Добавляем криптовалюты
        message += "\n🔗 Криптовалюты (Binance):\n"
        
        crypto_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
        for pair in crypto_pairs:
            try:
                response = requests.get(f"{BINANCE_API_URL}?symbol={pair}")
                crypto_data = response.json()
                price = float(crypto_data['price'])
                message += f"• {pair[:-4]}: ${price:.2f}\n"
            except:
                message += f"• {pair[:-4]}: недоступно\n"
        
        message += f"\n📅 Дата обновления: {data['Date'][:10]}"
        
    except Exception as e:
        print(f"Ошибка: {e}")
        message = "❌ Ошибка получения курсов. Попробуйте позже."

    await update.message.reply_text(message)

async def convert_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Для конвертации введите команду в формате:\n"
            "/convert <сумма> <из валюты> <в валюту>\n\n"
            "Например: /convert 100 USD RUB"
        )
        return
    
    try:
        amount = float(context.args[0])
        from_currency = context.args[1].upper()
        to_currency = context.args[2].upper()
        
        response = requests.get(CBR_API_URL)
        data = response.json()
        
        if from_currency == 'RUB':
            if to_currency not in data['Valute']:
                await update.message.reply_text("❌ Валюта не найдена")
                return
            
            rate = data['Valute'][to_currency]['Value']
            nominal = data['Valute'][to_currency]['Nominal']
            result = amount / (rate / nominal)
            await update.message.reply_text(
                f"💰 {amount} RUB = {result:.2f} {to_currency}\n"
                f"Курс: 1 {to_currency} = {rate/nominal:.2f} RUB"
            )
        
        elif to_currency == 'RUB':
            if from_currency not in data['Valute']:
                await update.message.reply_text("❌ Валюта не найдена")
                return
            
            rate = data['Valute'][from_currency]['Value']
            nominal = data['Valute'][from_currency]['Nominal']
            result = amount * (rate / nominal)
            await update.message.reply_text(
                f"💰 {amount} {from_currency} = {result:.2f} RUB\n"
                f"Курс: 1 {from_currency} = {rate/nominal:.2f} RUB"
            )
        
        else:
            if from_currency not in data['Valute'] or to_currency not in data['Valute']:
                await update.message.reply_text("❌ Валюта не найдена")
                return
            
            from_rate = data['Valute'][from_currency]['Value']
            from_nominal = data['Valute'][from_currency]['Nominal']
            to_rate = data['Valute'][to_currency]['Value']
            to_nominal = data['Valute'][to_currency]['Nominal']
            
            rub_amount = amount * (from_rate / from_nominal)
            result = rub_amount / (to_rate / to_nominal)
            
            await update.message.reply_text(
                f"💰 {amount} {from_currency} = {result:.2f} {to_currency}\n"
                f"Через RUB: 1 {from_currency} = {from_rate/from_nominal:.2f} RUB, "
                f"1 {to_currency} = {to_rate/to_nominal:.2f} RUB"
            )
    
    except Exception as e:
        print(f"Ошибка конвертации: {e}")
        await update.message.reply_text(
            "❌ Ошибка конвертации. Проверьте формат команды:\n"
            "/convert <сумма> <из валюты> <в валюту>\n\n"
            "Например: /convert 100 USD RUB"
        )

async def show_graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        keyboard = []
        row = []
        for i, currency in enumerate(POPULAR_CURRENCIES, 1):
            row.append(InlineKeyboardButton(currency, callback_data=f"graph_{currency}"))
            if i % 4 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите валюту для построения графика:", reply_markup=reply_markup)
        return
    
    currency = context.args[0].upper()
    await generate_currency_graph(update, context, currency)

async def generate_currency_graph(update: Update, context: ContextTypes.DEFAULT_TYPE, currency: str):
    try:
        end_date = datetime.datetime.now()
        start_date = end_date - timedelta(days=7)
        
        dates = []
        rates = []
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y/%m/%d")
            api_url = f"https://www.cbr-xml-daily.ru/archive/{date_str}/daily_json.js"
            
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if currency in data['Valute']:
                        rate = data['Valute'][currency]['Value']
                        nominal = data['Valute'][currency]['Nominal']
                        dates.append(current_date)
                        rates.append(rate / nominal)
            except:
                pass
            
            current_date += timedelta(days=1)
        
        if not dates:
            # Используем правильный способ отправки сообщения в зависимости от контекста
            if hasattr(update, 'message'):
                await update.message.reply_text("❌ Не удалось получить данные для построения графика")
            else:
                await update.callback_query.message.reply_text("❌ Не удалось получить данные для построения графика")
            return
        
        plt.figure(figsize=(10, 5))
        plt.plot(dates, rates, marker='o', linestyle='-')
        plt.title(f'Курс {currency} к RUB за последние 7 дней')
        plt.xlabel('Дата')
        plt.ylabel('Курс (RUB)')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        
        # Используем правильный способ отправки фото в зависимости от контекста
        if hasattr(update, 'message'):
            await update.message.reply_photo(
                photo=buf,
                caption=f"График курса {currency} к RUB за последние 7 дней"
            )
        else:
            await update.callback_query.message.reply_photo(
                photo=buf,
                caption=f"График курса {currency} к RUB за последние 7 дней"
            )
    
    except Exception as e:
        print(f"Ошибка построения графика: {e}")
        # Используем правильный способ отправки сообщения об ошибке
        if hasattr(update, 'message'):
            await update.message.reply_text("❌ Ошибка построения графика. Попробуйте позже.")
        else:
            await update.callback_query.message.reply_text("❌ Ошибка построения графика. Попробуйте позже.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('graph_'):
        currency = query.data.split('_')[1]
        # Передаем query вместо update для правильной обработки
        await generate_currency_graph(query, context, currency)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📋 Доступные команды:\n\n"
        "💰 Курсы валют - показать текущие курсы\n"
        "📊 Графики - построить график изменения курса\n"
        "🔄 Конвертер - конвертировать валюты\n\n"
        "Команды для конвертации:\n"
        "/convert <сумма> <из валюты> <в валюту>\n"
        "Например: /convert 100 USD RUB\n\n"
        "Команды для графиков:\n"
        "/graph <валюта> - построить график\n"
        "Например: /graph USD\n\n"
        "Поддерживаемые валюты: USD, EUR, GBP, JPY, CNY, CHF, CAD, AUD, SGD, HKD, TRY"
    )
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '💰 Курсы валют':
        await get_rates(update, context)
    elif text == '📊 Графики':
        await show_graph(update, context)
    elif text == '🔄 Конвертер':
        await update.message.reply_text(
            "Для конвертации введите команду в формате:\n"
            "/convert <сумма> <из валюты> <в валюту>\n\n"
            "Например: /convert 100 USD RUB"
        )
    elif text == 'ℹ️ Помощь':
        await help_command(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rates", get_rates))
    app.add_handler(CommandHandler("convert", convert_currency))
    app.add_handler(CommandHandler("graph", show_graph))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()