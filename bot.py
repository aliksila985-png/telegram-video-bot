import os
import asyncio
import yt_dlp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_links = {}
music_results = {}
user_lang = {}

# ======================
# ЯЗЫКИ

TEXTS = {
    "ru": {
        "start": "Привет 👋\n\nОтправь ссылку или название песни.",
        "help": "📌 Как пользоваться:\n\n1. Отправь ссылку\n2. Выбери видео или аудио\n\nИли просто напиши название песни.",
        "choose": "Что скачать?",
        "no_link": "Сначала отправь ссылку",
        "down_video": "⏳ Скачиваю видео...",
        "down_audio": "⏳ Скачиваю аудио...",
        "search": "🔎 Ищу песни...",
        "choose_num": "Напиши номер 1-5",
        "error": "❌ Ошибка. Попробуй другую ссылку или песню.",
        "cancel": "Отменено",
        "lang_set": "Язык установлен: Русский"
    },
    "en": {
        "start": "Hi 👋\n\nSend a link or song name.",
        "help": "📌 How to use:\n\n1. Send link\n2. Choose video or audio\n\nOr type a song name.",
        "choose": "What to download?",
        "no_link": "Send a link first",
        "down_video": "⏳ Downloading video...",
        "down_audio": "⏳ Downloading audio...",
        "search": "🔎 Searching songs...",
        "choose_num": "Type number 1-5",
        "error": "❌ Error. Try another link or song.",
        "cancel": "Cancelled",
        "lang_set": "Language set: English"
    }
}

def t(user_id, key):
    lang = user_lang.get(user_id, "ru")
    return TEXTS[lang][key]

# ======================
# КНОПКИ

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Видео"), KeyboardButton(text="🎵 Аудио")],
        [KeyboardButton(text="🔎 Поиск"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="🌐 Язык")]
    ],
    resize_keyboard=True
)

lang_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇬🇧 English")]
    ],
    resize_keyboard=True
)

# ======================
# START

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(t(message.from_user.id, "start"), reply_markup=main_kb)

# ======================
# HELP

@dp.message(lambda m: m.text == "❓ Помощь")
async def help_cmd(message: types.Message):
    await message.answer(t(message.from_user.id, "help"))

# ======================
# LANGUAGE

@dp.message(lambda m: m.text == "🌐 Язык")
async def lang(message: types.Message):
    await message.answer("Choose language:", reply_markup=lang_kb)

@dp.message(lambda m: m.text == "🇷🇺 Русский")
async def ru(message: types.Message):
    user_lang[message.from_user.id] = "ru"
    await message.answer(TEXTS["ru"]["lang_set"], reply_markup=main_kb)

@dp.message(lambda m: m.text == "🇬🇧 English")
async def en(message: types.Message):
    user_lang[message.from_user.id] = "en"
    await message.answer(TEXTS["en"]["lang_set"], reply_markup=main_kb)

# ======================
# ССЫЛКА

@dp.message(lambda m: m.text and "http" in m.text)
async def link(message: types.Message):
    user_links[message.from_user.id] = message.text
    await message.answer(t(message.from_user.id, "choose"))

# ======================
# СКАЧИВАНИЕ

def download(url, audio=False):

    os.makedirs("downloads", exist_ok=True)

    opts = {
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
    }

    if audio:
        opts["format"] = "bestaudio/best"
    else:
        opts["format"] = "best"

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if "entries" in info:
            info = info["entries"][0]

        return ydl.prepare_filename(info)

# ======================
# ВИДЕО

@dp.message(lambda m: m.text == "📥 Видео")
async def video(message: types.Message):

    url = user_links.get(message.from_user.id)

    if not url:
        await message.answer(t(message.from_user.id, "no_link"))
        return

    msg = await message.answer(t(message.from_user.id, "down_video"))

    try:
        file = download(url)
        await message.answer_video(FSInputFile(file))
    except:
        await message.answer(t(message.from_user.id, "error"))

    await msg.delete()

# ======================
# АУДИО

@dp.message(lambda m: m.text == "🎵 Аудио")
async def audio(message: types.Message):

    url = user_links.get(message.from_user.id)

    if not url:
        await message.answer(t(message.from_user.id, "no_link"))
        return

    msg = await message.answer(t(message.from_user.id, "down_audio"))

    try:
        file = download(url, True)
        await message.answer_audio(FSInputFile(file))
    except:
        await message.answer(t(message.from_user.id, "error"))

    await msg.delete()

# ======================
# ПОИСК

@dp.message(lambda m: m.text and "http" not in m.text)
async def search(message: types.Message):

    query = message.text
    msg = await message.answer(t(message.from_user.id, "search"))

    try:
        url = f"ytsearch5:{query} music"

        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        songs = info["entries"][:5]
        music_results[message.from_user.id] = songs

        text = "🎵\n\n"
        for i, s in enumerate(songs, 1):
            text += f"{i}. {s['title']}\n"

        text += "\n" + t(message.from_user.id, "choose_num")

        await message.answer(text)

    except:
        await message.answer(t(message.from_user.id, "error"))

    await msg.delete()

# ======================
# ВЫБОР

@dp.message(lambda m: m.text in ["1","2","3","4","5"])
async def choose(message: types.Message):

    songs = music_results.get(message.from_user.id)

    if not songs:
        return

    msg = await message.answer("⏳...")

    for song in songs:
        try:
            file = download(song["webpage_url"], True)
            await message.answer_audio(FSInputFile(file))
            await msg.delete()
            return
        except:
            continue

    await message.answer(t(message.from_user.id, "error"))
    await msg.delete()

# ======================
# RUN

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())