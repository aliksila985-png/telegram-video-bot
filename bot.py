import asyncio
import os
import yt_dlp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

TOKEN = "8667187883:AAH_xGaY7UqiPjRn8At5T6Ijf2de1KafKLs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_lang = {}
mode = {}

# Клавиатура RU
def menu_ru():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Скачать видео"), KeyboardButton(text="🎵 Скачать аудио")],
            [KeyboardButton(text="🎧 Найти музыку")],
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="🌍 Язык")]
        ],
        resize_keyboard=True
    )

# Клавиатура EN
def menu_en():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Download video"), KeyboardButton(text="🎵 Download audio")],
            [KeyboardButton(text="🎧 Find music")],
            [KeyboardButton(text="❓ Help"), KeyboardButton(text="🌍 Language")]
        ],
        resize_keyboard=True
    )

# START
@dp.message(CommandStart())
async def start(message: types.Message):

    user_lang[message.from_user.id] = "ru"

    text = (
        "👋 Добро пожаловать!\n\n"
        "Этот бот умеет:\n\n"
        "📥 скачивать видео\n"
        "🎵 скачивать аудио\n"
        "🎧 искать музыку\n\n"
        "Поддерживаемые платформы:\n"
        "• TikTok\n"
        "• Instagram\n"
        "• YouTube (Shorts и длинные видео)\n"
        "• Twitter/X\n"
        "• Snapchat"
    )

    await message.answer(text, reply_markup=menu_ru())

# помощь
@dp.message(lambda m: m.text in ["❓ Помощь", "❓ Help"])
async def help_command(message: types.Message):

    lang = user_lang.get(message.from_user.id, "ru")

    if lang == "ru":

        text = (
            "❓ Помощь\n\n"
            "📥 Отправьте ссылку чтобы скачать видео.\n"
            "🎵 Можно скачать только аудио.\n"
            "🎧 Можно искать музыку по названию.\n\n"

            "⚠️ Видео может не скачаться если:\n"
            "• видео приватное\n"
            "• аккаунт закрыт\n"
            "• ссылка неправильная\n"
            "• видео удалено\n"
            "• видео слишком длинное\n"
            "• медленный интернет"
        )

    else:

        text = (
            "❓ Help\n\n"
            "📥 Send a link to download video\n"
            "🎵 You can download audio\n"
            "🎧 You can search music\n\n"

            "⚠️ Download may fail if:\n"
            "• video is private\n"
            "• account is private\n"
            "• wrong link\n"
            "• video deleted\n"
            "• video too long\n"
            "• slow internet"
        )

    await message.answer(text)

# язык
@dp.message(lambda m: m.text in ["🌍 Язык", "🌍 Language"])
async def language(message: types.Message):

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Русский")],
            [KeyboardButton(text="English")]
        ],
        resize_keyboard=True
    )

    await message.answer("Выберите язык / Choose language", reply_markup=kb)

# выбор языка
@dp.message(lambda m: m.text in ["Русский", "English"])
async def set_lang(message: types.Message):

    if message.text == "Русский":

        user_lang[message.from_user.id] = "ru"
        await message.answer("Язык изменён", reply_markup=menu_ru())

    else:

        user_lang[message.from_user.id] = "en"
        await message.answer("Language changed", reply_markup=menu_en())

# скачать видео
@dp.message(lambda m: m.text in ["📥 Скачать видео", "📥 Download video"])
async def video_mode(message: types.Message):

    mode[message.from_user.id] = "video"

    if user_lang.get(message.from_user.id) == "en":
        await message.answer("Send video link.")
    else:
        await message.answer("Отправьте ссылку на видео.")

# скачать аудио
@dp.message(lambda m: m.text in ["🎵 Скачать аудио", "🎵 Download audio"])
async def audio_mode(message: types.Message):

    mode[message.from_user.id] = "audio"

    if user_lang.get(message.from_user.id) == "en":
        await message.answer("Send link.")
    else:
        await message.answer("Отправьте ссылку.")

# поиск музыки
@dp.message(lambda m: m.text in ["🎧 Найти музыку", "🎧 Find music"])
async def music_mode(message: types.Message):

    mode[message.from_user.id] = "music"

    if user_lang.get(message.from_user.id) == "en":
        await message.answer("Send music name.")
    else:
        await message.answer("Напишите название музыки.")

# обработка сообщений
@dp.message()
async def handle(message: types.Message):

    user_mode = mode.get(message.from_user.id)

    if user_mode == "music":

        query = f"ytsearch5:{message.text}"

        ydl_opts = {"quiet": True}

        try:

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(query, download=False)

                text = "🎧 Найдено:\n\n"

                for i, entry in enumerate(info["entries"], start=1):

                    text += f"{i}. {entry['title']}\n"
                    text += f"{entry['webpage_url']}\n\n"

                await message.answer(text)

        except:

            await message.answer("Ошибка поиска")

    elif user_mode in ["video", "audio"]:

        url = message.text

        status = await message.answer("⏳ Скачиваю...")

        if user_mode == "video":

            ydl_opts = {
                "format": "best",
                "outtmpl": "video.%(ext)s",
                "quiet": True
            }

        else:

            ydl_opts = {
                "format": "bestaudio",
                "outtmpl": "audio.%(ext)s",
                "quiet": True
            }

        try:

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(url, download=True)

                file = ydl.prepare_filename(info)

            await status.delete()

            media = FSInputFile(file)

            if user_mode == "video":
                await message.answer_video(media)
            else:
                await message.answer_audio(media)

            os.remove(file)

        except:

            await status.delete()

            await message.answer("❌ Ошибка скачивания")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())