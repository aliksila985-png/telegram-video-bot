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

# меню RU
def menu_ru():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="🌍 Язык")]
        ],
        resize_keyboard=True
    )

# меню EN
def menu_en():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Help"), KeyboardButton(text="🌍 Language")]
        ],
        resize_keyboard=True
    )

# старт
@dp.message(CommandStart())
async def start(message: types.Message):

    user_lang[message.from_user.id] = "ru"

    text = (
        "👋 Привет!\n\n"
        "Я помогаю скачивать видео и аудио из популярных платформ.\n\n"
        "Просто отправь ссылку, и я попробую скачать файл.\n\n"
        "Работаю с такими сервисами как:\n"
        "• YouTube (включая Shorts)\n"
        "• TikTok\n"
        "• Instagram\n"
        "• Twitter / X\n"
        "• Snapchat\n"
        "• Facebook\n\n"
        "И многими другими платформами."
    )

    await message.answer(text, reply_markup=menu_ru())

# помощь
@dp.message(lambda m: m.text in ["❓ Помощь", "❓ Help"])
async def help_command(message: types.Message):

    text = (
        "❓ Помощь\n\n"
        "Просто отправьте ссылку на видео, и бот попробует скачать его.\n\n"
        "Видео может не скачаться если:\n"
        "• видео приватное\n"
        "• аккаунт закрытый\n"
        "• ссылка неправильная\n"
        "• видео удалено\n"
        "• видео слишком длинное\n"
        "• медленный интернет"
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

# смена языка
@dp.message(lambda m: m.text in ["Русский", "English"])
async def set_lang(message: types.Message):

    if message.text == "Русский":

        user_lang[message.from_user.id] = "ru"

        await message.answer(
            "Язык изменён.",
            reply_markup=menu_ru()
        )

    else:

        user_lang[message.from_user.id] = "en"

        await message.answer(
            "Language changed.",
            reply_markup=menu_en()
        )

# обработка ссылок
import requests

@dp.message()
async def download(message: types.Message):

    url = message.text

    if "http" not in url:
        return

    status = await message.answer("⏳ Скачиваю...")

    try:

        # TikTok без watermark
        if "tiktok.com" in url:

            api = f"https://www.tikwm.com/api/?url={url}"

            r = requests.get(api).json()

            video_url = r["data"]["play"]

            video_data = requests.get(video_url).content

            with open("tiktok.mp4", "wb") as f:
                f.write(video_data)

            await status.delete()

            video = FSInputFile("tiktok.mp4")

            await message.answer_video(video)

            os.remove("tiktok.mp4")

            return

        # остальные платформы
        opts = {
            "format": "best",
            "outtmpl": "video.%(ext)s",
            "quiet": True
        }

        with yt_dlp.YoutubeDL(opts) as ydl:

            info = ydl.extract_info(url, download=True)

            file = ydl.prepare_filename(info)

        await status.delete()

        video = FSInputFile(file)

        await message.answer_video(video)

        os.remove(file)

    except:

        await status.delete()

        await message.answer("❌ Не получилось скачать видео.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())