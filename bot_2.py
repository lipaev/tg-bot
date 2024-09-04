from key import key
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from aiogram import F
import requests

bot = Bot(key)
dp = Dispatcher()


@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message):
    await message.answer(
        "Привет!\nМогу прислать картинку с животным\nили просто напиши мне что-нибудь"
    )


@dp.message(Command(commands=["help"]))
async def process_start_command(message: Message):
    await message.answer(
        "/fox - пришлёт лисичку\n/dog - пришлёт собачку\n/cat - пришлёт котика"
    )


@dp.message(Command(commands=["fox"]))
async def send_fox(message: Message):
    await message.answer_photo(
        requests.get("https://randomfox.ca/floof").json()["image"],
        caption=f"{message.from_user.first_name}, ваша лисичка",
    )


@dp.message(Command(commands=["cat"]))
async def send_cat(message: Message):
    await message.answer_photo(
        requests.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"],
        caption=f"{message.from_user.first_name}, ваш котик",
    )


@dp.message(Command(commands=["dog"]))
async def send_dog(message: Message):
    await message.answer_photo(
        requests.get("https://random.dog/woof.json").json()["url"],
        caption=f"{message.from_user.first_name}, ваша собачка",
    )


@dp.message(F.content_type == ContentType.TEXT)
async def send_text(message: Message):
    await message.answer(
        f'{message.from_user.first_name}, ваше сообщение\n"{message.text}"\nбыло отправлено {message.date.date()} в {message.date.time()}.'
    )


@dp.message(F.content_type == ContentType.PHOTO)
async def send_photo(message: Message):
    print(message.photo)
    await message.answer_photo(message.photo[-1].file_id, caption=message.caption)


@dp.message(F.sticker)
async def send_sticker(message: Message):
    print(message.sticker)
    await message.answer_sticker(message.sticker.file_id, caption=message.caption)


@dp.message()
async def send_copy(message: Message):
    try:
        await message.send_copy(message.chat.id)
    except TypeError:
        await message.reply("Извините, но сообщение не распознано.")


if __name__ == "__main__":
    dp.run_polling(bot)
