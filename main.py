import os
import requests

from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, KICKED
from aiogram.types import Message, ContentType, ChatMemberUpdated, PhotoSize
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv
from asyncio import sleep
from google.generativeai.types.generation_types import IncompleteIterationError
import pandas as pd

from filters import IsAdmin
from mylibr.aicom import question_answer, chat_with_history, ask_gemini
from mylibr.features import convert_gemini_to_markdown_v1, convert_gemini_to_markdown_v2 as cgtmv2

load_dotenv()


bot = Bot(os.getenv('KEY'))
dp = Dispatcher()
df = pd.read_csv('users.csv', index_col='id')

async def answer_start(message: Message):
    df.loc[message.from_user.id, 'block'] = 0
    df.loc[message.from_user.id, ['first_name', 'block', 'stream']] = [message.from_user.first_name, 0, 0]
    df.to_csv('users.csv')
    print(message.from_user.id, message.from_user.first_name, "blocked the bot")
    await message.answer(
        "Привет!\nЯ - бот-помощник.\nУмею общаться и делиться картинками.\nДля дополнительной информации отправь - /help!"
    )

async def answer_help(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.answer(
        f"/fox - пришлёт лисичку\n/dog - пришлёт собачку\n/cat - пришлёт котика\n/stream - {'Включает режим генерации сообщений для ответов ИИ.'if df.stream[message.from_user.id] else "Отключает режим генерации сообщений для ответов ИИ."}"
    )#\n\n/partnership - Для сотрудничества
    if message.from_user.id in eval(os.environ.get('ADMIN_IDS')):
        await message.answer("Для администратора:\n/all")

async def answer_change_generation(message: Message):
    df.stream[message.from_user.id] = not df.stream[message.from_user.id]
    df.to_csv('users.csv')
    await message.answer(f"{'Режим генерации сообщений для ответов ИИ активирован.'if df.stream[message.from_user.id] else "Режим генерации сообщений для ответов ИИ деактивирован."}")

async def answer_partnership(message: Message):
    # сделать так, чтобы пользователь мог написать создателю
    await bot.send_chat_action(message.chat.id, "typing")
    await message.answer("По вопросам сотрудничества обращайтесь к lipaeev")

async def send_fox(message: Message):
    await bot.send_chat_action(message.chat.id, "upload_photo")
    await message.answer_photo(
        requests.get("https://randomfox.ca/floof").json()["image"],
        caption=f"{message.from_user.first_name}, ваша лисичка",
    )

async def send_cat(message: Message):
    await bot.send_chat_action(message.chat.id, "upload_photo")
    await message.answer_photo(
        requests.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"],
        caption=f"{message.from_user.first_name}, ваш котик",
    )

async def send_dog(message: Message):
    await bot.send_chat_action(message.chat.id, "upload_photo")
    await message.answer_photo(
        requests.get("https://random.dog/woof.json").json()["url"],
        caption=f"{message.from_user.first_name}, ваша собачка",
    )

async def send_all_pic(message: Message):
    await bot.send_chat_action(message.chat.id, "upload_photo")
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

async def send_gemini_text(message: Message):
    async def send_stream_text(message: Message, temp_text: str='', stream: bool=df.stream[message.from_user.id]):
        if not stream:
            text=ask_gemini(message).text
            print(text + '\n' + '*' * 160)
            text=cgtmv2(text)
            print(text)
            try:
                await message.answer(text=text, parse_mode='MarkdownV2')
            except TelegramBadRequest as TGB:
                bad_request = f'{TGB}. Попробуйте ещё раз.'
                if 'message is too long' in str(TGB):
                    try:
                        await message.answer(text[:text[:len(text) // 2].rfind('\n\n')], parse_mode='MarkdownV2')
                        await sleep(2)
                        await message.answer(text[text[:len(text) // 2].rfind('\n\n'):], parse_mode='MarkdownV2')
                    except TelegramBadRequest:
                        await message.answer(bad_request)
                elif "parse entities" in str(TGB):
                    try:
                        await message.answer(text[:len(text) // 2])
                        await sleep(2)
                        await message.answer(text[len(text) // 2:])
                    except TelegramBadRequest:
                        await message.answer(bad_request)
                else:
                    await message.answer(bad_request)
        else:
            for chunk in ask_gemini(message, stream):
                if temp_text:
                    temp_text += chunk.text
                    temp_text = convert_gemini_to_markdown_v1(temp_text)
                    print(chunk.text, end='')
                    try:
                        await message_1.edit_text(temp_text, parse_mode='Markdown')
                    except TelegramBadRequest:
                        await message_1.edit_text(temp_text)
                else:
                    temp_text += chunk.text
                    temp_text = convert_gemini_to_markdown_v1(temp_text)
                    print(chunk.text, end='')
                    try:
                        message_1 = await bot.send_message(message.chat.id, temp_text, parse_mode="Markdown")
                    except TelegramBadRequest:
                        message_1 = await bot.send_message(message.chat.id, temp_text)
            print('*' * 80, temp_text)
    #await show_typing(bot, message.chat.id)
    await bot.send_chat_action(message.chat.id, "typing")
    try:
        await send_stream_text(message)
    except IncompleteIterationError:
        print(IncompleteIterationError.mro())
        await send_stream_text(message)

async def send_course_ai_reply(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.answer(chat_with_history(message))

async def send_photo(message: Message, mphoto: PhotoSize):
    await bot.send_chat_action(message.chat.id, "upload_photo")
    print(mphoto)
    await message.answer_photo(mphoto.file_id, caption=message.caption)

async def send_sticker(message: Message):
    await bot.send_chat_action(message.chat.id, "choose_sticker")
    print(message.sticker)
    await message.answer_sticker(message.sticker.file_id, caption=message.caption)

async def send_copy(message: Message):
    try:
        await message.send_copy(message.chat.id)
    except TypeError:
        await message.reply("Извините, но сообщение не распознано.")

async def block(event: ChatMemberUpdated):
    df.loc[event.from_user.id, 'block'] = 1
    df.to_csv('users.csv')
    print(event.from_user.id, event.from_user.first_name, "blocked the bot")

dp.message.register(answer_start, CommandStart())
dp.message.register(answer_help, Command(commands=["help"]))
dp.message.register(answer_change_generation, (Command(commands=["stream"])))
dp.message.register(answer_partnership, Command(commands=["partnership"]))
dp.message.register(send_fox, Command(commands=["fox"]))
dp.message.register(send_cat, Command(commands=["cat"]))
dp.message.register(send_dog, Command(commands=["dog"]))
dp.message.register(send_all_pic, IsAdmin(), Command(commands=["all"]))
dp.message.register(send_course_ai_reply, F.content_type == ContentType.TEXT)
dp.message.register(send_photo, F.photo[-1].as_("mphoto"))  # F.content_type == 'photo' or F.photo or lambda m: m.photo
dp.message.register(send_sticker, lambda m: m.sticker)
dp.message.register(send_copy)
dp.my_chat_member.register(block, ChatMemberUpdatedFilter(KICKED))

if __name__ == "__main__":
    dp.run_polling(bot)
