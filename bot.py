import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import os

BOT_TOKEN = os.getenv("8667187883:AAH_xGaY7UqiPjRn8At5T6Ijf2de1KafKLs")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_links = {}

# Главное меню
menu = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🔎 Поиск музыки")],
        [types.KeyboardButton(text="❓ Помощь"), types.KeyboardButton(text="🌐 Язык")]
    ],
    resize_keyboard=True
)

# Кнопки выбора
download_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📹 Скачать видео", callback_data="video"),
            InlineKeyboardButton(text="🎵 Скачать аудио", callback_data="audio")
        ]
    ]
)


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! 👋\n\n"
        "Я бот, который скачивает видео и аудио из:\n"
        "• YouTube\n"
        "• YouTube Shorts\n"
        "• TikTok\n"
        "• Instagram\n\n"
        "Просто отправь ссылку на видео.",
        reply_markup=menu
    )


@dp.message(lambda message: message.text == "❓ Помощь")
async def help(message: types.Message):
    await message.answer(
        "Если видео не скачивается, возможны причины:\n\n"
        "• видео слишком длинное\n"
        "• приватное видео\n"
        "• платформа временно блокирует скачивание\n"
        "• проблемы с интернетом сервера\n\n"
        "Просто отправьте ссылку снова."
    )


@dp.message(lambda message: message.text == "🌐 Язык")
async def language(message: types.Message):
    await message.answer("Скоро появится больше языков 🌍")


# Поиск музыки
@dp.message(lambda message: message.text == "🔎 Поиск музыки")
async def music_search(message: types.Message):
    await message.answer("Напишите название песни 🎵")


def search_music(query):
    ydl_opts = {
        "quiet": True,
        "default_search": "ytsearch5"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(query, download=False)
        return result["entries"]


@dp.message()
async def handle_message(message: types.Message):

    text = message.text

    if "http" in text:
        user_links[message.from_user.id] = text

        await message.answer(
            "Что вы хотите скачать?",
            reply_markup=download_keyboard
        )
        return

    # поиск музыки
    results = search_music(text)

    response = "🎵 Найдено:\n\n"

    for video in results:
        response += f"{video['title']}\n{video['webpage_url']}\n\n"

    await message.answer(response)


@dp.callback_query()
async def download(callback: types.CallbackQuery):

    url = user_links.get(callback.from_user.id)

    if not url:
        await callback.message.answer("Ссылка не найдена")
        return

    wait = await callback.message.answer("⏳ Скачиваю...")

    if callback.data == "video":
        ydl_opts = {
            "outtmpl": "video.%(ext)s"
        }

    else:
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": "audio.%(ext)s"
        }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file = os.listdir()[0]

        await callback.message.answer_document(types.FSInputFile(file))

        os.remove(file)

    except:
        await callback.message.answer("❌ Ошибка скачивания")

    await wait.delete()


async def main():
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())