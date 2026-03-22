import logging
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==== Load environment variables ====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не знайдено або він некоректний. Перевір .env файл і токен від @BotFather.")

# ==== Google Sheets setup ====
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
GSPREAD_CLIENT = gspread.authorize(CREDS)
SHEET = GSPREAD_CLIENT.open("MoodTracker").sheet1

# ==== Logging ====
logging.basicConfig(level=logging.INFO)

# ==== States ====
(
    SLEEP, ENERGY, MOOD, ANXIETY, MEANING, SPEED,
    IRRITABILITY, SOCIAL, IMPULSIVITY, SOMATIC, COMMENT
) = range(11)

user_data = {}

# ==== Helpers ====
def analyze_phase(energy, mood, irritability, speed, sleep, meaning, social, impulsivity):
    sleep_weights = {
        "дуже мало": -2,
        "мало": -1,
        "нормально": 1,
        "багато": 0,
        "дуже багато": -1,
        "розбудіть": -2
    }
    sleep_score = next((v for k, v in sleep_weights.items() if sleep.startswith(k)), 0)

    weighted_score = (
        energy * 1.2 +
        mood * 1.2 +
        meaning * 1.0 +
        social * 0.8 +
        impulsivity * 1.5 +
        irritability * 1.3 +
        sleep_score
    )

    if weighted_score >= 40 and speed == 'пришвидшена':
        return 'Гіпоманія', weighted_score
    elif weighted_score <= 28 and speed == 'повільна':
        return 'Депресія', weighted_score
    elif weighted_score <= 33 and speed == 'нормальна':
        return 'Змішана', weighted_score
    else:
        return 'Нейтральна', weighted_score

async def send_start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Почати запис", callback_data='start_entry')]]
    markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Привіт! Я бот для трекінгу настрою.",
        reply_markup=markup
    )

async def start_entry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    reply_keyboard = [["дуже мало 💤", "мало"], ["нормально", "багато"], ["дуже багато", "розбудіть мене завтра"]]
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Скільки годин ти спав сьогодні?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return SLEEP

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/entry – внести дані\n/stats – подивитись графік (у розробці)\n/phase – пояснення фаз\n/help – допомога")

entry = start_entry_callback

async def sleep_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['date'] = datetime.now().strftime("%Y-%m-%d")
    user_data['sleep'] = update.message.text.split()[0]
    reply_keyboard = [[str(i) for i in range(1, 6)], [str(i) for i in range(6, 11)]]
    await update.message.reply_text("Оціни енергію (1–10):", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return ENERGY

async def energy_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['energy'] = int(update.message.text)
    reply_keyboard = [[str(i) for i in range(1, 6)], [str(i) for i in range(6, 11)]]
    await update.message.reply_text("Оціни настрій (1–10):", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return MOOD

async def mood_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['mood'] = int(update.message.text)
    reply_keyboard = [[str(i) for i in range(1, 6)], [str(i) for i in range(6, 11)]]
    await update.message.reply_text("Оціни тривогу (1–10):", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return ANXIETY

async def anxiety_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['anxiety'] = int(update.message.text)
    reply_keyboard = [[str(i) for i in range(1, 6)], [str(i) for i in range(6, 11)]]
    await update.message.reply_text("Оціни сенс / мотивацію (1–10):", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return MEANING

async def meaning_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['meaning'] = int(update.message.text)
    reply_keyboard = [["повільна 🐢", "нормальна ⚖️", "пришвидшена ⚡"]]
    await update.message.reply_text("Яка швидкість мислення?", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return SPEED

async def speed_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['speed'] = update.message.text.split()[0]
    reply_keyboard = [[str(i) for i in range(1, 6)], [str(i) for i in range(6, 11)]]
    await update.message.reply_text("Оціни дратівливість (1–10):", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return IRRITABILITY

async def irritability_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['irritability'] = int(update.message.text)
    reply_keyboard = [[str(i) for i in range(1, 6)], [str(i) for i in range(6, 11)]]
    await update.message.reply_text("Оціни соціальну активність (1–10):", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return SOCIAL

async def social_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['social'] = int(update.message.text)
    reply_keyboard = [[str(i) for i in range(1, 6)], [str(i) for i in range(6, 11)]]
    await update.message.reply_text("Оціни імпульсивність (1–10):", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return IMPULSIVITY

async def impulsivity_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['impulsivity'] = int(update.message.text)
    await update.message.reply_text("Є соматичні симптоми? (текстом або -):")
    return SOMATIC

async def somatic_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['somatic'] = update.message.text
    await update.message.reply_text("Коментарі (будь-що важливе):")
    return COMMENT

async def comment_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data['comment'] = update.message.text

    phase, weighted_score = analyze_phase(
        user_data['energy'],
        user_data['mood'],
        user_data['irritability'],
        user_data['speed'],
        user_data['sleep'],
        user_data['meaning'],
        user_data['social'],
        user_data['impulsivity']
    )

    row = [
        user_data['date'], user_data['sleep'], user_data['energy'], user_data['mood'], user_data['anxiety'],
        user_data['meaning'], user_data['speed'], user_data['irritability'], user_data['social'],
        user_data['impulsivity'], user_data['somatic'], user_data['comment'], phase
    ]
    SHEET.append_row(row)

    await update.message.reply_text(f"Дані збережено. Визначена фаза: {phase}. Total Score: {round(weighted_score, 1)}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Запис скасовано.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_entry_callback, pattern='^start_entry$')],
        states={
            SLEEP: [MessageHandler(filters.TEXT & ~filters.COMMAND, sleep_input)],
            ENERGY: [MessageHandler(filters.TEXT & ~filters.COMMAND, energy_input)],
            MOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, mood_input)],
            ANXIETY: [MessageHandler(filters.TEXT & ~filters.COMMAND, anxiety_input)],
            MEANING: [MessageHandler(filters.TEXT & ~filters.COMMAND, meaning_input)],
            SPEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, speed_input)],
            IRRITABILITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, irritability_input)],
            SOCIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, social_input)],
            IMPULSIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, impulsivity_input)],
            SOMATIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, somatic_input)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('start', send_start_menu))

    print("✅ MoodBot запущено")
    app.run_polling()
