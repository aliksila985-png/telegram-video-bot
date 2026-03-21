import os
import asyncio
import yt_dlp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_links = {}
music_results = {}
user_lang = {}

# =======================
# ТЕКСТЫ

TEXTS = {
    "ru": {
        "start": "👋 Привет!\n\n"
                 "Я могу:\n"
                 "• Скачать видео или аудио с YouTube, TikTok, Instagram\n"
                 "• Найти песню по названию\n\n"
                 "📌 Просто отправь ссылку или напиши название песни.",
        "help": "📌 Как пользоваться:\n\n"
                "1. Отправь ссылку → выбери видео или аудио\n"
                "2. Напиши название песни → выбери номер\n\n"
                "Поддерживаются:\nYouTube, TikTok, Instagram",
        "choose": "Что скачать?",
        "no_link": "Сначала отправь ссылку",
        "video": "⏳ Скачиваю видео...",
        "audio": "⏳ Скачиваю аудио...",
        "search": "🔎 Ищу песни...",
        "choose_num": "Напиши номер 1-5",
        "error": "❌ Ошибка. Попробуй другую ссылку или песню",
        "lang": "Язык установлен: Русский"
    },
    "en": {
        "start": "👋 Hi!\n\n"
                 "I can:\n"
                 "• Download video/audio from YouTube, TikTok, Instagram\n"
                 "• Find songs by name\n\n"
                 "📌 Send a link or type a song name.",
        "help": "📌 How to use:\n\n"
                "1. Send a link → choose video or audio\n"
                "2. Type song name → choose number",
        "choose": "What to download?",
        "no_link": "Send link first",
        "video": "⏳ Downloading video...",
        "audio": "⏳ Downloading audio...",
        "search": "🔎 Searching songs...",
        "choose_num": "Type number 1-5",
        "error": "❌ Error. Try another link or song",
        "lang": "Language set: English"
    }
}

def t(uid, key):
    return TEXTS[user_lang.get(uid, "ru")][key]

# =======================
# КНОПКИ

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="🌐 Язык")]
    ],
    resize_keyboard=True
)

choice_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Видео"), KeyboardButton(text="🎵 Аудио")]
    ],
    resize_keyboard=True
)

lang_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇬🇧 English")]
    ],
    resize_keyboard=True
)

# =======================
# START

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(t(message.from_user.id, "start"), reply_markup=main_kb)

# =======================
# HELP

@dp.message(lambda m: m.text == "❓ Помощь")
async def help_cmd(message: types.Message):
    await message.answer(t(message.from_user.id, "help"))

# =======================
# LANGUAGE

@dp.message(lambda m: m.text == "🌐 Язык")
async def lang(message: types.Message):
    await message.answer("Choose language:", reply_markup=lang_kb)

@dp.message(lambda m: m.text == "🇷🇺 Русский")
async def ru(message: types.Message):
    user_lang[message.from_user.id] = "ru"
    await message.answer(TEXTS["ru"]["lang"], reply_markup=main_kb)

@dp.message(lambda m: m.text == "🇬🇧 English")
async def en(message: types.Message):
    user_lang[message.from_user.id] = "en"
    await message.answer(TEXTS["en"]["lang"], reply_markup=main_kb)

# =======================
# ССЫЛКА

@dp.message(lambda m: m.text and "http" in m.text)
async def link(message: types.Message):

    user_links[message.from_user.id] = message.text

    await message.answer(
        t(message.from_user.id, "choose"),
        reply_markup=choice_kb
    )

# =======================
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

# =======================
# ВИДЕО

@dp.message(lambda m: m.text == "📥 Видео")
async def video(message: types.Message):

    url = user_links.get(message.from_user.id)

    if not url:
        await message.answer(t(message.from_user.id, "no_link"))
        return

    msg = await message.answer(t(message.from_user.id, "video"))

    try:
        file = download(url)
        await message.answer_video(FSInputFile(file))
    except:
        await message.answer(t(message.from_user.id, "error"))

    await msg.delete()

# =======================
# АУДИО

@dp.message(lambda m: m.text == "🎵 Аудио")
async def audio(message: types.Message):

    url = user_links.get(message.from_user.id)

    if not url:
        await message.answer(t(message.from_user.id, "no_link"))
        return

    msg = await message.answer(t(message.from_user.id, "audio"))

    try:
        file = download(url, True)
        await message.answer_audio(FSInputFile(file))
    except:
        await message.answer(t(message.from_user.id, "error"))

    await msg.delete()

# =======================
# ПОИСК МУЗЫКИ

@dp.message(lambda m: m.text and "http" not in m.text and m.text not in ["1","2","3","4","5"])
async def search(message: types.Message):

    msg = await message.answer(t(message.from_user.id, "search"))

    try:
        url = f"ytsearch5:{message.text} music"

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

# =======================
# ВЫБОР ПЕСНИ

@dp.message(lambda m: m.text in ["1","2","3","4","5"])
async def choose(message: types.Message):

    songs = music_results.get(message.from_user.id)

    if not songs:
        return

    msg = await message.answer("⏳...")

    for s in songs:
        try:
            file = download(s["webpage_url"], True)
            await message.answer_audio(FSInputFile(file))
            await msg.delete()
            return
        except:
            continue

    await message.answer(t(message.from_user.id, "error"))
    await msg.delete()

# =======================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())