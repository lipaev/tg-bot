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
from mylibr.aicom import history_chat as hc, history_chat_stream as hcs, chains, store
from mylibr.features import convert_gemini_to_markdown_v1, convert_gemini_to_markdown_v2 as cgtmv2

load_dotenv()


bot = Bot(os.getenv('VEAPIL_BOT'))
dp = Dispatcher()
df = pd.read_csv('users.csv', index_col='id')
admins_ids = eval(os.environ.get('ADMIN_IDS'))
models = {'flash': 'Gemini 1.5 Flash', 'pro': 'Gemini 1.5 Pro', 'mini': 'GPT 4o Mini'}
#ids_msgs_edit_model = []
#ids_msgs_edit_stream = []

async def answer_start(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    df.loc[message.from_user.id] = [message.from_user.first_name, 0, False, 'flash', message.from_user.language_code]
    df.to_csv('users.csv')
    print(message.from_user.id, message.from_user.first_name, "The user launched the bot.")
    await message.answer(
        "Приветствую!\nЯ - бот с искусственным интеллектом.\nУмею общаться и делиться картинками.\nДля дополнительной информации отправьте - /help!"
    )

async def answer_help(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.answer(
        f"/fox - пришлёт лисичку\n/dog - пришлёт собачку\n/cat - пришлёт котика\n/info - информация о настройках бота\n/stream - {'Включает режим стриминга сообщений ответов ИИ.' if df.stream[message.from_user.id] else "Отключает режим стриминга сообщений ответов ИИ."} (не доступно)"
    )#\n\n/partnership - Для сотрудничества
    if message.from_user.id in admins_ids:
        await message.answer("Для администратора:\n/mini\n/flash\n/pro")

async def change_stream(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    df.loc[message.from_user.id, 'stream'] = not df.stream[message.from_user.id]
    df.to_csv('users.csv')
    await message.answer(f"{'Режим стриминга сообщений для ответов ИИ активирован.'if df.stream[message.from_user.id] else "Режим стриминга сообщений для ответов ИИ деактивирован."}")

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

async def answer_info(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.answer(f"Ваша модель: {models[df.loc[message.from_user.id, 'model']]}\nСтриминг: {'✅' if df.stream[message.from_user.id] else '❎'}")

async def change_model(message: Message):
    if message.from_user.id in admins_ids:
        df.loc[message.from_user.id, 'model'] = message.text[1:]
        await message.answer(f"Модель обновлена на {models[df.loc[message.from_user.id, 'model']]}.")
    else:
        await message.answer("Доступно только администраторам.")

async def send_gemini_text(message: Message):
    async def send_stream_text(message: Message, temp_text: str='', stream: bool = False): #df.stream[message.from_user.id]
        if not stream:
            coroutine = await hc(message, df.loc[message.from_user.id].model)
            #print(text.content + '\n' + '*' * 160)
            text = cgtmv2(coroutine.content)
            print(text, f'\nTOTAL_TOKENS = {coroutine.usage_metadata['total_tokens']}', len(text))
            try:
                await message.answer(text=text, parse_mode='MarkdownV2')
            except TelegramBadRequest as TGB:
                bad_request = f'{TGB}.\nПопробуйте ещё раз.'
                if 'message is too long' in str(TGB):
                    try:
                        await message.answer(text[:text[:len(text) // 2].rfind('\n\n')], parse_mode='MarkdownV2')
                        await sleep(1)
                        await message.answer(text[text[:len(text) // 2].rfind('\n\n'):], parse_mode='MarkdownV2')
                    except TelegramBadRequest:
                        await message.answer(bad_request)
                elif "parse entities" in str(TGB):
                    try:
                        await message.answer(text[:len(text) // 2])
                        await sleep(1)
                        await message.answer(text[len(text) // 2:])
                    except TelegramBadRequest:
                        await message.answer(bad_request)
                else:
                    await message.answer(bad_request)
        else:
            for chunk in await hcs(message, df.loc[message.from_user.id].model):
                total_tokens = 0
                if temp_text:
                    temp_text += chunk.content
                    total_tokens += chunk.usage_metadata['total_tokens']
                    temp_text = convert_gemini_to_markdown_v1(temp_text)
                    #print(chunk.content, end='')
                    try:
                        await message_1.edit_text(temp_text, parse_mode='Markdown')
                    except TelegramBadRequest:
                        await message_1.edit_text(temp_text)
                else:
                    temp_text += chunk.content
                    total_tokens += chunk.usage_metadata['total_tokens']
                    temp_text = convert_gemini_to_markdown_v1(temp_text)
                    print(chunk.content, end='')
                    try:
                        message_1 = await bot.send_message(message.chat.id, temp_text, parse_mode="Markdown")
                    except TelegramBadRequest:
                        message_1 = await bot.send_message(message.chat.id, temp_text)
            print('*' * 160 + '\n', temp_text, f'\nTOTAL_TOKENS = {total_tokens}', len(temp_text))
    #await show_typing(bot, message.chat.id)
    await bot.send_chat_action(message.chat.id, "typing")
    try:
        await send_stream_text(message)
    except IncompleteIterationError:
        print(IncompleteIterationError.mro())
        await send_stream_text(message)

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
dp.message.register(change_stream, (Command(commands=["stream"])))
dp.message.register(answer_partnership, Command(commands=["partnership"]))
dp.message.register(answer_info, Command(commands=["info"]))
dp.message.register(change_model, Command(commands=["mini", "flash", "pro"]))
dp.message.register(send_fox, Command(commands=["fox"]))
dp.message.register(send_cat, Command(commands=["cat"]))
dp.message.register(send_dog, Command(commands=["dog"]))
dp.message.register(send_gemini_text, F.content_type == ContentType.TEXT)
dp.message.register(send_photo, F.photo[-1].as_("mphoto"))  # F.content_type == 'photo' or F.photo or lambda m: m.photo
dp.message.register(send_sticker, lambda m: m.sticker)
dp.message.register(send_copy)
dp.my_chat_member.register(block, ChatMemberUpdatedFilter(KICKED))

if __name__ == "__main__":
    dp.run_polling(bot)
