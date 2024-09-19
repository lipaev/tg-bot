import os
import requests
from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, KICKED
from aiogram.types import Message, ContentType, ChatMemberUpdated, PhotoSize
from dotenv import load_dotenv

from filters import IsAdmin
from aicom import ask_ai

load_dotenv()


bot = Bot(os.getenv('KEY'))
dp = Dispatcher()


@dp.message(CommandStart())
async def answer_start(message: Message):
    await message.answer(
        "Привет! Могу прислать картинку с животным или просто отправь мне что угодно и я отвечу тем же!"
        "\nДля дополнительной информации отправь - /help"
    )


@dp.message(Command(commands=["help"]))
async def answer_help(message: Message):
    await message.answer(
        "/fox - пришлёт лисичку\n/dog - пришлёт собачку\n/cat - пришлёт котика"
    )
    if message.from_user.id in eval(os.environ.get('ADMIN_IDS')):
        await message.answer("Для администратора:\n/all")


@dp.message(IsAdmin(), Command(commands=["all"]))
async def answer_all(message: Message):
    await message.answer_photo(
        requests.get("https://randomfox.ca/floof").json()["image"]
    )
    await message.answer_photo(
        requests.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"]
    )
    await message.answer_photo(
        requests.get("https://random.dog/woof.json").json()["url"],
        caption="Питомцы администратора",
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
    await message.answer(ask_ai(message.text))


@dp.message(
    F.photo[-1].as_("mphoto")
)  # F.content_type == 'photo' or F.photo or lambda m: m.photo
async def send_photo(message: Message, mphoto: PhotoSize):
    print(mphoto)
    await message.answer_photo(mphoto.file_id, caption=message.caption)


@dp.message(lambda m: m.sticker)
async def send_sticker(message: Message):
    print(message.sticker)
    await message.answer_sticker(message.sticker.file_id, caption=message.caption)


@dp.message()
async def send_copy(message: Message):
    try:
        await message.send_copy(message.chat.id)
    except TypeError:
        await message.reply("Извините, но сообщение не распознано.")


@dp.my_chat_member(ChatMemberUpdatedFilter(KICKED))
async def block(event: ChatMemberUpdated):
    print(event)
    print(
        event.from_user.id,
        event.from_user.first_name,
        "blocked the bot",
        f"\n{event.new_chat_member.user.id}, {event.new_chat_member.user.first_name}",
    )


if __name__ == "__main__":
    dp.run_polling(bot)
