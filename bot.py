import os
import asyncio
import yt_dlp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_links = {}

# =========================
# клавиатуры

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="🌐 Язык")]
    ],
    resize_keyboard=True
)

choice_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Видео"), KeyboardButton(text="🎵 Аудио")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True
)

# =========================
# START

@dp.message(Command("start"))
async def start(message: types.Message):

    text = (
        "Привет 👋\n\n"
        "Я бот который скачивает видео и аудио из:\n"
        "• YouTube (включая Shorts)\n"
        "• TikTok\n"
        "• Instagram\n"
        "• Snapchat\n\n"
        "Отправь ссылку на видео\n"
        "или напиши название музыки."
    )

    await message.answer(text, reply_markup=main_kb)

# =========================
# HELP

@dp.message(lambda m: m.text == "❓ Помощь")
async def help_cmd(message: types.Message):

    text = (
        "Если видео не скачалось:\n\n"
        "• видео слишком длинное\n"
        "• приватный пост\n"
        "• ошибка сети\n"
        "• сайт временно ограничил доступ\n\n"
        "Попробуйте другую ссылку."
    )

    await message.answer(text)

# =========================
# LANGUAGE

@dp.message(lambda m: m.text == "🌐 Язык")
async def lang(message: types.Message):

    await message.answer(
        "Language feature coming soon 🌐\n"
        "Скоро будет выбор языка."
    )

# =========================
# если отправили ссылку

@dp.message(lambda m: m.text and "http" in m.text)
async def get_link(message: types.Message):

    user_links[message.from_user.id] = message.text

    await message.answer(
        "Что скачать?",
        reply_markup=choice_kb
    )

# =========================
# функция скачивания

def download_media(url, audio=False):

    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "noplaylist": True,
        "quiet": True
    }

    if audio:
        ydl_opts["format"] = "bestaudio/best"
    else:
        ydl_opts["format"] = "best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)

    return file

# =========================
# скачать видео

@dp.message(lambda m: m.text == "📥 Видео")
async def send_video(message: types.Message):

    url = user_links.get(message.from_user.id)

    if not url:
        await message.answer("Сначала отправь ссылку.")
        return

    msg = await message.answer("⏳ Скачиваю видео...")

    try:

        file = download_media(url, audio=False)

        await message.answer_video(FSInputFile(file))

    except Exception as e:

        await message.answer(f"Ошибка: {e}")

    await msg.delete()

# =========================
# скачать аудио

@dp.message(lambda m: m.text == "🎵 Аудио")
async def send_audio(message: types.Message):

    url = user_links.get(message.from_user.id)

    if not url:
        await message.answer("Сначала отправь ссылку.")
        return

    msg = await message.answer("⏳ Скачиваю аудио...")

    try:

        file = download_media(url, audio=True)

        await message.answer_audio(FSInputFile(file))

    except Exception as e:

        await message.answer(f"Ошибка: {e}")

    await msg.delete()

# =========================
# отмена

@dp.message(lambda m: m.text == "❌ Отмена")
async def cancel(message: types.Message):

    await message.answer("Отменено.", reply_markup=main_kb)

# =========================
# поиск музыки

@dp.message()
async def music_search(message: types.Message):

    query = message.text

    msg = await message.answer("🔎 Ищу музыку...")

    try:

        search = f"ytsearch:{query}"

        file = download_media(search, audio=True)

        await message.answer_audio(FSInputFile(file))

    except:

        await message.answer("Не удалось найти музыку.")

    await msg.delete()

# =========================
# запуск

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())