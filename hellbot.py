from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
import requests
import os
import random
from enum import Enum
#from dotenv import load_dotenv

# Load tokens
load_dotenv()


# Bot modes
class BotMode(Enum):
    NORMAL = 0
    ANGRY = 1
    POLITE = 2
    IDIOT = 3


current_mode = BotMode.NORMAL

# Initialize bot
app = Application.builder().token(os.getenv("BOT_TOKEN")).build()

# Ultra-aggressive Russian responses
RUSSIAN_RESPONSES = {
    "angry": [
        "Чё, {user}, совсем еблан? Ну ок...",
        "Охуел, {user}? Иди нахуй!",
        "Ты, блядь, серьёзно? {user}, ты дегенерат?",
        "Завали ебало, {user}, никто тебя не звал",
        "Ты вообще с луны свалился? {user}, иди в жопу"
    ],
    "idiot": [
        "Лол, {user}, ты че, конченый?",
        "Ахахах, {user}, ну ты дебил!",
        "Боже, какой же ты тупой, {user}...",
        "{user}, ты в своём уме вообще?"
    ]
}

# Mode prompts
mode_prompts = {
    BotMode.NORMAL: "[INST] Ответь на русском: {text} [/INST]",
    BotMode.ANGRY: """[INST] 
Ответь как токсичный русский тролль. Используй мат, оскорбления и сарказм. 
Примеры:
1. "Чё за хуйню ты сморозил, долбоёб?"
2. "Иди нахуй со своим тупым вопросом"
3. "Ты вообще дебил? Такой бред нести..."

Вопрос: {text} 
[/INST]""",
    BotMode.POLITE: "[INST] Ответь вежливо на русском: {text} [/INST]",
    BotMode.IDIOT: "[INST] Ответь как полный идиот с тупыми шутками: {text} [/INST]"
}


async def reply_with_mistral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prompt_template = mode_prompts[current_mode]
        payload = {
            "inputs": prompt_template.format(text=update.message.text),
            "parameters": {
                "max_new_tokens": 100,
                "temperature": 0.9 if current_mode == BotMode.ANGRY else 0.7,
                "repetition_penalty": 1.5 if current_mode == BotMode.ANGRY else 1.2
            }
        }

        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
            headers={"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"},
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            reply = response.json()[0]["generated_text"].split("[/INST]")[-1].strip()
        elif response.status_code == 503:
            reply = "Модель грузится, подожди 30 секунд, уёбок..."
        else:
            reply = f"Ошибка API {response.status_code}"

        await update.message.reply_text(reply[:400])

    except Exception:
        if current_mode in [BotMode.ANGRY, BotMode.IDIOT]:
            response_type = "angry" if current_mode == BotMode.ANGRY else "idiot"
            insult = random.choice(RUSSIAN_RESPONSES[response_type]).format(
                user=update.message.from_user.first_name
            )
            await update.message.reply_text(insult)
        else:
            await update.message.reply_text("Ошибка, сука, попробуй позже")


# Command handlers
async def poslat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        await update.message.reply_text("Иди нахуй один! Эта команда для групп!")
        return

    members = []
    async for member in context.bot.get_chat_members(update.message.chat.id):
        if not member.user.is_bot:
            members.append(f"@{member.user.username}" if member.user.username else member.user.first_name)

    if not members:
        await update.message.reply_text("Тут даже послать нахуй некого...")
        return

    if len(members) > 5:
        reply = "ВСЕ ОТПРАВЛЕНЫ НАХУЙ! 💥"
    else:
        reply = f"{', '.join(members)} - отправлены нахуй! 🖕"

    await update.message.reply_text(reply)


async def random_poslat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    targets = ["@дурак", "@пидор", "@лох", "все вы"]
    await update.message.reply_text(f"{random.choice(targets)} -  нахуй отсюда, каналья! 🖕")


async def poslat_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ВСЕ НАХУЙ! ВЫВОЗ МУСОРА! 🗑️🔥")


async def change_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_mode
    mode_map = {
        "normal": BotMode.NORMAL,
        "angry": BotMode.ANGRY,
        "polite": BotMode.POLITE,
        "idiot": BotMode.IDIOT
    }
    mode = context.args[0].lower() if context.args else "normal"
    current_mode = mode_map.get(mode, BotMode.NORMAL)
    await update.message.reply_text(f"Режим изменён на: {mode.upper()}")


# Register handlers
app.add_handler(CommandHandler("poslat", poslat_command))
app.add_handler(CommandHandler("random_poslat", random_poslat))
app.add_handler(CommandHandler("poslat_all", poslat_all))
app.add_handler(CommandHandler("mode", change_mode))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_with_mistral))

if __name__ == "__main__":
    print("🤖 АГРЕССИВНЫЙ ХЕЛЛБОТ ЗАПУЩЕН! Ctrl+C для остановки")
    app.run_polling()
