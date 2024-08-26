from key import key
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from aiogram import F

bot = Bot(key)
dp = Dispatcher()


@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message):
    await message.answer(
        "Привет!\nЯ - Эхо-бот!\nНапиши мне что-нибудь и я повторю за тобой!"
    )


@dp.message(Command(commands=["help"]))
async def process_start_command(message: Message):
    await message.answer("Я бот-попугай, повторю почти любое сообщение за тобой.")


@dp.message(F.content_type == ContentType.PHOTO)
async def send_photo(message: Message):
    print(message.photo)
    await message.answer_photo(message.photo[-1].file_id)


@dp.message(F.sticker)
async def send_sticker(message: Message):
    print(message.sticker)
    await message.reply_sticker(message.sticker.file_id)


@dp.message()
async def send_copy(message: Message):
    try:
        await message.send_copy(message.chat.id)
    except TypeError:
        await message.reply("Извините, но сообщение не распознано.")


if __name__ == "__main__":
    dp.run_polling(bot)
