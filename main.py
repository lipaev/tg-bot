import os
import requests
import asyncio
import logging
import pandas as pd
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, KICKED
from aiogram.types import Message, ContentType, ChatMemberUpdated, PhotoSize
from aiogram.exceptions import TelegramBadRequest

from mylibr.filters import WritingOnFile
from mylibr.aicom import history_chat as hc, history_chat_stream as hcs, store, InMemoryHistory
from mylibr.features import convert_gemini_to_markdown_v1 as cgtmv1, convert_gemini_to_markdown_v2 as cgtmv2, show_typing

load_dotenv()
bot = Bot(os.getenv('TIPTOP_IBOT'))
dp = Dispatcher()
df = pd.read_csv('users.csv', index_col='id')
admins_ids = eval(os.environ.get('ADMIN_IDS'))
models = {'flash': 'Gemini 1.5 Flash', 'pro': 'Gemini 1.5 Pro', 'mini': 'GPT 4o Mini'}
handler = logging.FileHandler('logs.log', mode='w', encoding='utf-8')
handler.addFilter(WritingOnFile())
logging.basicConfig(level=logging.DEBUG,
                    format='{asctime}|{levelname:7}|{filename}:{lineno}|{name}|  {message}',
                    style='{',
                    handlers=[handler, logging.StreamHandler()])


async def answer_start(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    df.loc[message.from_user.id] = [message.from_user.first_name, 0, False, 'flash', message.from_user.language_code]
    df.to_csv('users.csv')
    logging.info(f"{message.from_user.id}, {message.from_user.first_name}, {message.from_user.language_code}")
    await message.answer(
        "Приветствую!\nЯ - бот с искусственным интеллектом.\nУмею общаться и делиться картинками.\nДля дополнительной информации отправьте - /help!"
    )

async def answer_help(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.answer(
        f"Ваша модель: {models[df.loc[message.from_user.id, 'model']]}\nСтриминг сообщений ИИ: {'✅' if df.stream[message.from_user.id] else '❎'}\n\nКоманды:\n/stream - {'Отключает режим стриминга ответов ИИ.' if df.stream[message.from_user.id] else "Включает режим стриминга ответов ИИ."}\n/fox - пришлёт лисичку\n/dog - пришлёт собачку\n/cat - пришлёт котика\n/clear - забыть историю сообщений"
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

async def change_model(message: Message):
    if message.from_user.id in admins_ids:
        df.loc[message.from_user.id, 'model'] = message.text[1:]
        df.to_csv('users.csv')
        await message.answer(f"Модель обновлена на {models[df.loc[message.from_user.id, 'model']]}.")
    else:
        await message.answer("Пока доступно только администраторам.")

async def clear_history(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    store[message.from_user.id] = InMemoryHistory()
    await message.answer("История очищена.")

async def answer_langchain(message: Message):
    async def send_stream_text(message: Message, stream: bool = df.stream[message.from_user.id]):
        if not stream or df.loc[message.from_user.id, 'model'] == 'mini':
            basemessage = await hc(message, df.loc[message.from_user.id].model)
            text = cgtmv2(basemessage.content)
            print('*' * 160 + '\n', text, f'\nTOTAL_TOKENS = {basemessage.usage_metadata['total_tokens']}', len(text))
            while True:
                if len(text) <= 4096:
                    await message.answer(text, parse_mode='MarkdownV2')
                    break
                else:
                    cut = text[0:4096].rfind('\n\n')
                    temporary, text = text[:cut], text[cut:]
                    await message.answer(temporary, parse_mode='MarkdownV2')
            stop_event.set()
        else:
            temp_text = ''
            total_tokens = 0
            total_len = 0
            response = await hcs(message, df.loc[message.from_user.id].model)
            for chunk in response:
                if temp_text:
                    temp_text += chunk.content
                    total_len += len(chunk.content)
                    total_tokens += chunk.usage_metadata['output_tokens']
                    temp_text = cgtmv1(temp_text)
                    if len(temp_text) <= 4096:
                        try:
                            await message_1.edit_text(temp_text, parse_mode='Markdown')
                        except TelegramBadRequest:
                            if "message is not modified" in str(TelegramBadRequest):
                                pass
                    else:
                        cut = temp_text[0:4096].rfind('\n\n')
                        temporary, temp_text = temp_text[:cut], temp_text[cut:]
                        try:
                            await message_1.edit_text(temporary, parse_mode="Markdown")
                        except TelegramBadRequest:
                            if "message is not modified" in str(TelegramBadRequest):
                                pass
                        message_1 = await bot.send_message(message.chat.id, temp_text, parse_mode='Markdown')
                else:
                    temp_text += chunk.content
                    total_len += len(chunk.content)
                    total_tokens += chunk.usage_metadata['total_tokens']
                    temp_text = cgtmv1(temp_text)
                    message_1 = await bot.send_message(message.chat.id, temp_text, parse_mode="Markdown")
                    stop_event.set()
            print('*' * 160 + '\n', temp_text, f'\nTOTAL_TOKENS = {total_tokens} LENGTH = {total_len}')
    stop_event = asyncio.Event()
    try:
        await asyncio.gather(show_typing(bot, message.chat.id, stop_event, duration=60), send_stream_text(message))
    except TelegramBadRequest:
        logging.error(str(TelegramBadRequest))
    finally:
        stop_event.set()

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
dp.message.register(change_model, Command(commands=["mini", "flash", "pro"]))
dp.message.register(clear_history, Command(commands=["clear"]))
dp.message.register(send_fox, Command(commands=["fox"]))
dp.message.register(send_cat, Command(commands=["cat"]))
dp.message.register(send_dog, Command(commands=["dog"]))
dp.message.register(answer_langchain, F.content_type == ContentType.TEXT)
dp.message.register(send_photo, F.photo[-1].as_("mphoto"))  # F.content_type == 'photo' or F.photo or lambda m: m.photo
dp.message.register(send_sticker, lambda m: m.sticker)
dp.message.register(send_copy)
dp.my_chat_member.register(block, ChatMemberUpdatedFilter(KICKED))

if __name__ == "__main__":
    dp.run_polling(bot)
