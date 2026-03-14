import os
import asyncio
import yt_dlp
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

# =========================
# TOKEN
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_links = {}
search_results = {}

# =========================
# Клавиатуры
main_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❓ Помощь"), KeyboardButton(text="🌐 Язык")]],
    resize_keyboard=True
)

choice_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📥 Видео"), KeyboardButton(text="🎵 Аудио")],
              [KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True
)

music_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1️⃣"), KeyboardButton(text="2️⃣"), KeyboardButton(text="3️⃣")],
        [KeyboardButton(text="4️⃣"), KeyboardButton(text="5️⃣")],
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
        "Отправь ссылку на видео или напиши название песни."
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
        "• сайт ограничил доступ\n"
    )
    await message.answer(text)

# =========================
# LANGUAGE
@dp.message(lambda m: m.text == "🌐 Язык")
async def lang(message: types.Message):
    await message.answer("Скоро будет выбор языка.")

# =========================
# если отправили ссылку
@dp.message(lambda m: m.text and "http" in m.text)
async def get_link(message: types.Message):
    user_links[message.from_user.id] = message.text
    await message.answer("Что скачать?", reply_markup=choice_kb)

# =========================
# скачивание медиа
def download_media(url, audio=False):
    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "ignoreerrors": True
    }
    if audio:
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio","preferredcodec": "mp3","preferredquality": "192"}]
    else:
        ydl_opts["format"] = "best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise Exception("Видео недоступно")
        file_path = ydl.prepare_filename(info)
        if audio:
            file_path = os.path.splitext(file_path)[0] + ".mp3"
    return file_path

# =========================
# СКАЧАТЬ ВИДЕО
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
# СКАЧАТЬ АУДИО
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
# ПОИСК МУЗЫКИ
@dp.message(lambda m: m.text not in ["❓ Помощь","🌐 Язык","📥 Видео","🎵 Аудио","❌ Отмена","1️⃣","2️⃣","3️⃣","4️⃣","5️⃣"])
async def search_music(message: types.Message):
    query = message.text
    msg = await message.answer("🔎 Ищу музыку...")
    try:
        ydl_opts = {"quiet": True,"ignoreerrors": True,"extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            results = [v for v in info["entries"] if v]
        if not results:
            await message.answer("Ничего не найдено.")
            return
        search_results[message.from_user.id] = results
        text = "Нашёл варианты:\n\n"
        for i, video in enumerate(results[:5]):
            text += f"{i+1}. {video['title']}\n"
        await message.answer(text, reply_markup=music_kb)
    except Exception as e:
        await message.answer(f"Ошибка поиска: {e}")
    await msg.delete()

# =========================
# ВЫБОР ПЕСНИ
@dp.message(lambda m: m.text in ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣"])
async def choose_music(message: types.Message):
    index = int(message.text[0]) - 1
    results = search_results.get(message.from_user.id)
    if not results:
        await message.answer("Сначала напиши название песни.")
        return
    url = results[index]["webpage_url"]
    msg = await message.answer("⏳ Скачиваю музыку...")
    try:
        file = download_media(url, audio=True)
        await message.answer_audio(FSInputFile(file))
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
    await msg.delete()

# =========================
# ОТМЕНА
@dp.message(lambda m: m.text == "❌ Отмена")
async def cancel(message: types.Message):
    await message.answer("Отменено.", reply_markup=main_kb)

# =========================
# ЗАПУСК
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())