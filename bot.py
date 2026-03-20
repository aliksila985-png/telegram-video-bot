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

# ======================
# КЛАВИАТУРЫ

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

# ======================
# START

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет 👋\n\n"
        "Отправь ссылку или название песни.",
        reply_markup=main_kb
    )

# ======================
# ПОМОЩЬ

@dp.message(lambda m: m.text == "❓ Помощь")
async def help_cmd(message: types.Message):
    await message.answer("Отправь ссылку или название песни.")

# ======================
# ССЫЛКА

@dp.message(lambda m: m.text and "http" in m.text)
async def link(message: types.Message):

    user_links[message.from_user.id] = message.text

    await message.answer("Что скачать?", reply_markup=choice_kb)

# ======================
# СКАЧИВАНИЕ (ФИКС С ANDROID)

def download(url, audio=False):

    os.makedirs("downloads", exist_ok=True)

    opts = {
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,

        # 🔥 ВАЖНЫЙ ФИКС
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },

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

        file = ydl.prepare_filename(info)

    return file

# ======================
# ВИДЕО

@dp.message(lambda m: m.text == "📥 Видео")
async def video(message: types.Message):

    url = user_links.get(message.from_user.id)

    if not url:
        await message.answer("Сначала отправь ссылку")
        return

    msg = await message.answer("⏳ Скачиваю видео...")

    try:
        file = download(url)
        await message.answer_video(FSInputFile(file))
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

    await msg.delete()

# ======================
# АУДИО

@dp.message(lambda m: m.text == "🎵 Аудио")
async def audio(message: types.Message):

    url = user_links.get(message.from_user.id)

    if not url:
        await message.answer("Сначала отправь ссылку")
        return

    msg = await message.answer("⏳ Скачиваю аудио...")

    try:
        file = download(url, True)
        await message.answer_audio(FSInputFile(file))
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

    await msg.delete()

# ======================
# ОТМЕНА

@dp.message(lambda m: m.text == "❌ Отмена")
async def cancel(message: types.Message):
    await message.answer("Отменено", reply_markup=main_kb)

# ======================
# ПОИСК МУЗЫКИ

@dp.message(lambda m: m.text and "http" not in m.text and m.text not in ["1","2","3","4","5"])
async def search(message: types.Message):

    query = message.text
    msg = await message.answer("🔎 Ищу песни...")

    try:

        url = f"ytsearch5:{query} official audio"

        opts = {
            "quiet": True,
            "nocheckcertificate": True,
            "geo_bypass": True,

            # 🔥 тот же фикс
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"]
                }
            },
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        songs = info["entries"][:5]
        music_results[message.from_user.id] = songs

        text = "🎵 Найдено:\n\n"

        for i, song in enumerate(songs, 1):
            text += f"{i}. {song['title']}\n"

        text += "\nНапиши 1-5"

        await message.answer(text)

    except Exception as e:
        await message.answer(f"Ошибка поиска: {e}")

    await msg.delete()

# ======================
# ВЫБОР ПЕСНИ

@dp.message(lambda m: m.text in ["1","2","3","4","5"])
async def choose(message: types.Message):

    songs = music_results.get(message.from_user.id)

    if not songs:
        return

    index = int(message.text) - 1

    msg = await message.answer("⏳ Скачиваю...")

    try:
        url = songs[index]["webpage_url"]
        file = download(url, True)
        await message.answer_audio(FSInputFile(file))
    except:
        await message.answer("❌ Ошибка скачивания")

    await msg.delete()

# ======================
# ЗАПУСК

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())