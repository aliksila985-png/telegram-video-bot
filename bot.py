import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import yt_dlp

# ==========================
# Получаем токен из переменных среды
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if BOT_TOKEN is None or BOT_TOKEN.strip() == "":
    raise Exception("BOT_TOKEN not found in environment variables")
BOT_TOKEN = BOT_TOKEN.strip()
print("TOKEN LOADED:", BOT_TOKEN[:10])

# ==========================
# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================
# Клавиатура
kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Помощь"), KeyboardButton(text="Язык")],
    ],
    resize_keyboard=True
)

# ==========================
# Старт команды
@dp.message(Command(commands=["start"]))
async def start(message: types.Message):
    await message.answer(
        "Привет! Этот бот позволяет скачивать видео и аудио с:\n"
        "- YouTube (включая Shorts)\n"
        "- TikTok\n"
        "- Instagram\n"
        "- Snapchat\n\n"
        "Просто отправь ссылку на видео или название музыки, и бот предложит варианты.",
        reply_markup=kb
    )

# ==========================
# Помощь
@dp.message(lambda m: m.text.lower() == "помощь")
async def help_cmd(message: types.Message):
    await message.answer(
        "Возможные причины ошибок:\n"
        "- Видео слишком длинное\n"
        "- Платформа недоступна или ограничена\n"
        "- Ошибка сети или таймаут\n"
        "- Неверная ссылка\n\n"
        "Попробуйте повторить или использовать VPN, если платформа заблокирована в вашей стране."
    )

# ==========================
# Изменение языка (пример)
@dp.message(lambda m: m.text.lower() == "язык")
async def language_cmd(message: types.Message):
    await message.answer("Выберите язык / Choose language:\n1. Русский\n2. English")

# ==========================
# Вспомогательная функция для скачивания видео/аудио
async def download_media(url, audio_only=False):
    out_dir = "downloads"
    os.makedirs(out_dir, exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best" if audio_only else "best",
        "outtmpl": f"{out_dir}/%(title)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
    return file_path

# ==========================
# Обработка сообщений с ссылкой или названием музыки
@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()
    
    # Если это ссылка на видео
    if text.startswith("http"):
        # Спросим, что скачать
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Видео"), KeyboardButton(text="Аудио")],
                [KeyboardButton(text="Отмена")]
            ],
            resize_keyboard=True
        )
        await message.answer("Что вы хотите скачать?", reply_markup=keyboard)
        # Сохраняем url в пользовательский state
        dp.data = {message.from_user.id: text}
        return

    # Если это музыка (по названию)
    if len(text.split()) > 0:
        # Используем yt_dlp поиск
        search_url = f"ytsearch5:{text}"
        try:
            file_path = await download_media(search_url, audio_only=True)
            await message.answer_document(open(file_path, "rb"))
        except Exception as e:
            await message.answer(f"Ошибка при поиске музыки: {e}")

# ==========================
# Обработка выбора "Видео" или "Аудио"
@dp.message(lambda m: m.text in ["Видео", "Аудио"])
async def handle_choice(message: types.Message):
    url = dp.data.get(message.from_user.id)
    if not url:
        await message.answer("Ссылка не найдена. Отправьте ссылку ещё раз.")
        return

    audio_only = message.text == "Аудио"
    await message.answer("Скачиваю, подождите...")
    try:
        file_path = await download_media(url, audio_only=audio_only)
        await message.answer_document(open(file_path, "rb"))
    except Exception as e:
        await message.answer(f"Ошибка при скачивании: {e}")
    finally:
        # Очистим state пользователя
        dp.data.pop(message.from_user.id, None)

# ==========================
# Запуск бота
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))