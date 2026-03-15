import os
import asyncio
import yt_dlp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

# =========================
# TOKEN
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not found in environment variables")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =========================
# Память
user_links = {}       # ссылки для скачивания
music_results = {}    # результаты поиска музыки

# =========================
# Клавиатуры
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
        "Я бот, который скачивает видео и аудио из:\n"
        "• YouTube (включая Shorts)\n"
        "• TikTok\n"
        "• Instagram\n"
        "• Snapchat\n\n"
        "Отправь ссылку на видео\n"
        "или напиши название песни."
    )
    await message.answer(text, reply_markup=main_kb)

# =========================
# HELP
@dp.message(lambda m: m.text == "❓ Помощь")
async def help_cmd(message: types.Message):
    text = (
        "Если видео или музыка не скачались:\n\n"
        "• видео может быть удалено\n"
        "• видео может быть заблокировано\n"
        "• видео приватное\n"
        "• ошибка сети\n\n"
        "Попробуй другую ссылку или другую песню."
    )
    await message.answer(text)

# =========================
# LANGUAGE
@dp.message(lambda m: m.text == "🌐 Язык")
async def lang(message: types.Message):
    await message.answer("Выбор языка скоро появится 🌐")

# =========================
# Если отправили ссылку
@dp.message(lambda m: m.text and "http" in m.text)
async def get_link(message: types.Message):
    user_links[message.from_user.id] = message.text
    await message.answer("Что скачать?", reply_markup=choice_kb)

# =========================
# Функция скачивания
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

        file_path = ydl.prepare_filename(info)

    return file_path

# =========================
# Скачать видео
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
# Скачать аудио
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
# Отмена
@dp.message(lambda m: m.text == "❌ Отмена")
async def cancel(message: types.Message):
    await message.answer("Отменено.", reply_markup=main_kb)

# =========================
# Поиск музыки
@dp.message(lambda m: m.text and "http" not in m.text and m.text not in ["1","2","3","4","5"])
async def search_music(message: types.Message):

    query = message.text
    msg = await message.answer("🔎 Ищу песни...")

    try:

        url = f"ytsearch5:{query}"

        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        songs = []

        for entry in info["entries"]:
            title = entry["title"].lower()

            if "official" in title or "audio" in title or "topic" in title:
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
# Выбор песни
@dp.message(lambda m: m.text in ["1","2","3","4","5"])
async def choose_song(message: types.Message):

    songs = music_results.get(message.from_user.id)

    if not songs:
        await message.answer("Сначала найди песню.")
        return

    index = int(message.text) - 1

    msg = await message.answer("⏳ Скачиваю песню...")

    for i in range(index, len(songs)):

        try:

            url = songs[i]["webpage_url"]

            file = download_media(url, audio=True)

            await message.answer_audio(FSInputFile(file))

            await msg.delete()
            return

        except:
            continue

    await message.answer("❌ Не удалось скачать песню.")
    await msg.delete()

# =========================
# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())