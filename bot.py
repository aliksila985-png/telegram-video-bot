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
music_results = {}

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
        "• YouTube\n"
        "• TikTok\n"
        "• Instagram\n\n"
        "Отправь ссылку или название песни."
    )

    await message.answer(text, reply_markup=main_kb)

# =========================
# HELP

@dp.message(lambda m: m.text == "❓ Помощь")
async def help_cmd(message: types.Message):

    await message.answer(
        "Отправь ссылку на видео или название песни."
    )

# =========================
# LANGUAGE

@dp.message(lambda m: m.text == "🌐 Язык")
async def lang(message: types.Message):

    await message.answer("Функция языка скоро появится.")

# =========================
# если ссылка

@dp.message(lambda m: m.text and "http" in m.text)
async def get_link(message: types.Message):

    user_links[message.from_user.id] = message.text

    await message.answer(
        "Что скачать?",
        reply_markup=choice_kb
    )

# =========================
# скачивание

def download_media(url, audio=False):

    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True
    }

    if audio:
        ydl_opts["format"] = "bestaudio/best"
    else:
        ydl_opts["format"] = "best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=True)

        if "entries" in info:
            info = info["entries"][0]

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

        file = download_media(url)

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

@dp.message(lambda m: m.text and "http" not in m.text)
async def search_music(message: types.Message):

    query = message.text

    msg = await message.answer("🔎 Ищу песни...")

    try:

        url = f"ytsearch5:{query}"

        ydl_opts = {"quiet": True}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=False)

        songs = []

        for entry in info["entries"]:

            title = entry["title"]

            if "music" in title.lower() or "official" in title.lower() or "topic" in title.lower():
                songs.append(entry)

        if not songs:
            songs = info["entries"][:5]

        music_results[message.from_user.id] = songs

        text = "🎵 Найденные песни:\n\n"

        for i, song in enumerate(songs, 1):

            text += f"{i}. {song['title']}\n"

        text += "\nНапиши номер 1-5"

        await message.answer(text)

    except Exception as e:

        await message.answer(f"Ошибка поиска: {e}")

    await msg.delete()

# =========================
# выбор песни

@dp.message(lambda m: m.text in ["1","2","3","4","5"])
async def choose_song(message: types.Message):

    songs = music_results.get(message.from_user.id)

    if not songs:
        return

    index = int(message.text) - 1

    if index >= len(songs):
        return

    url = songs[index]["webpage_url"]

    msg = await message.answer("⏳ Скачиваю песню...")

    try:

        file = download_media(url, audio=True)

        await message.answer_audio(FSInputFile(file))

    except Exception as e:

        await message.answer(f"Ошибка: {e}")

    await msg.delete()

# =========================
# запуск

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())