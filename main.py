import requests
import asyncio
import logging
import pandas as pd

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, KICKED
from aiogram.types import Message, ContentType, ChatMemberUpdated, PhotoSize, BotCommand, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk

from mylibr.filters import WritingOnFile
from mylibr.aicom import history_chat as hc, history_chat_stream as hcs, store, InMemoryHistory
from mylibr.features import convert_gemini_to_markdown_v1 as cgtmv1, convert_gemini_to_markdown_v2 as cgtmv2, show_typing
from mylibr.keyboards import keyboard_help
from config import config


bot = Bot(config.tg_bot.token)
dp = Dispatcher()
df = pd.read_csv('users.csv', index_col='id')
store.update(dict(zip(df.index, map(lambda x: eval(x)[0], df['history'].to_dict().values()))))
models = {'flash': 'Gemini 1.5 Flash', 'pro': 'Gemini 1.5 Pro', 'mini': 'GPT 4o Mini', 'english': 'Учитель английского'}
handler = logging.FileHandler('logs.log', mode='w', encoding='utf-8')
handler.addFilter(WritingOnFile())
logging.basicConfig(level=logging.DEBUG,
                    format='{asctime}|{levelname:7}|{filename}:{lineno}|{name}|  {message}',
                    style='{',
                    handlers=[handler, logging.StreamHandler()])


async def answer_start(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()
    df.loc[message.from_user.id] = [message.from_user.first_name,
                                    0,
                                    False,
                                    'flash',
                                    message.from_user.language_code,
                                    str([InMemoryHistory()])]
    df.to_csv('users.csv')
    logging.info(f"{message.from_user.id}, {message.from_user.first_name}, {message.from_user.language_code}")
    await message.answer(
        "*Приветствую!*\nЯ - бот с искусственным интеллектом.\nУмею общаться и делиться картинками.\nДля дополнительной информации отправь - /help!", parse_mode='Markdown'
    )

async def answer_help(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()
    stream = df.stream[message.from_user.id]
    await message.answer(
        f"""Ваша модель: {models[df.loc[message.from_user.id, 'model']]}
Стриминг ответов ИИ: {'✅' if stream else '❎'}

*Команды*:
/stream - {'Отключает режим стриминга ответов ИИ.' if stream else "Включает режим стриминга ответов ИИ."}
/fox - пришлёт лисичку
/dog - пришлёт собачку
/cat - пришлёт котика
/clear - забыть историю сообщений""",
        reply_markup=keyboard_help(stream),
        parse_mode='Markdown'
    )#\n\n/partnership - Для сотрудничества
    if message.from_user.id in config.tg_bot.admin_ids:
        await message.answer("Для разработчиков:\n/mini /flash /pro /english")

async def callback_help(callback: CallbackQuery):
    if callback.data == 'clear':
        store[callback.message.chat.id] = InMemoryHistory()
        await callback.answer("История очищена.")
    elif '❎' in callback.message.text:
        df.loc[callback.message.chat.id, 'stream'] = True
        df.to_csv('users.csv')
        await callback.message.edit_text(
            callback.message.text.replace('❎', '✅').replace('Команды:', '*Команды*:'),
            reply_markup=keyboard_help(True),
            parse_mode='Markdown')
        await callback.answer("Стриминг активирован.")
    else:
        df.loc[callback.message.chat.id, 'stream'] = False
        df.to_csv('users.csv')
        await callback.message.edit_text(
            callback.message.text.replace('✅', '❎').replace('Команды:', '*Команды*:'),
            reply_markup=keyboard_help(),
            parse_mode='Markdown')
        await callback.answer("Стриминг деактивирован.")

async def change_stream(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()
    df.loc[message.from_user.id, 'stream'] = not df.stream[message.from_user.id]
    df.to_csv('users.csv')
    await message.answer(f"{'Режим стриминга сообщений для ответов ИИ активирован.'if df.stream[message.from_user.id] else "Режим стриминга сообщений для ответов ИИ деактивирован."}")

async def answer_partnership(message: Message):
    # сделать так, чтобы пользователь мог написать создателю
    await bot.send_chat_action(message.chat.id, "typing")
    await message.answer("По вопросам сотрудничества обращайтесь к lipaeev")

async def send_fox(message: Message):
    await bot.send_chat_action(message.chat.id, "upload_photo")
    await message.delete()
    await message.answer_photo(
        requests.get("https://randomfox.ca/floof").json()["image"],
        caption=f"{message.from_user.first_name}, ваша лисичка",
    )

async def send_cat(message: Message):
    await bot.send_chat_action(message.chat.id, "upload_photo")
    await message.delete()
    await message.answer_photo(
        requests.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"],
        caption=f"{message.from_user.first_name}, ваш котик",
    )

async def send_dog(message: Message):
    await bot.send_chat_action(message.chat.id, "upload_photo")
    await message.delete()
    await message.answer_photo(
        requests.get("https://random.dog/woof.json").json()["url"],
        caption=f"{message.from_user.first_name}, ваша собачка",
    )

async def callback_pets(callback: CallbackQuery):
    if callback.data == 'fox':
        await callback.message.answer_photo(
            requests.get("https://randomfox.ca/floof").json()["image"],
            caption=f"{callback.message.chat.first_name}, ваша 🦊 лисичка",
        )
        await callback.answer()
    elif callback.data == 'dog':
        await callback.message.answer_photo(
            requests.get("https://random.dog/woof.json").json()["url"],
            caption=f"{callback.message.chat.first_name}, ваша 🐶 собачка",
        )
        await callback.answer()
    elif callback.data == 'cat':
        await callback.message.answer_photo(
            requests.get("https://api.thecatapi.com/v1/images/search").json()[0]["url"],
            caption=f"{callback.message.chat.first_name}, ваш 🐈 котик ",
        )
        await callback.answer()

async def change_model(message: Message):
    if message.from_user.id in config.tg_bot.admin_ids:
        df.loc[message.from_user.id, 'model'] = message.text[1:]
        df.to_csv('users.csv')
        await message.delete()
        await message.answer(f"Модель обновлена на {models[df.loc[message.from_user.id, 'model']]}.")
    else:
        await message.delete()
        await message.answer("Пока доступно только администраторам.")

async def clear_history(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()
    store[message.from_user.id] = InMemoryHistory()
    await message.answer("История очищена.")
    df.loc[message.from_user.id, 'history'] = str([InMemoryHistory()])
    df.to_csv('users.csv')

async def answer_langchain(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    async def send_stream_text(message: Message, stream: bool = df.stream[message.from_user.id]):
        if not stream or df.loc[message.from_user.id, 'model'] == 'mini':
            basemessage = await hc(message, df.loc[message.from_user.id].model)
            text = cgtmv2(basemessage.content)
            logging.debug(text)
            logging.info(f'TOTAL_TOKENS={basemessage.usage_metadata['total_tokens']} LENGTH={len(text)}')
            while True:
                if len(text) <= 4096:
                    try:
                        await message.answer(text, parse_mode='MarkdownV2')
                        break
                    except TelegramBadRequest:
                        logging.warning(str(TelegramBadRequest) + '||' + 'send_stream_text')
                        await message.answer(text, parse_mode='Markdown')
                        break
                else:
                    cut = text[0:4096].rfind('\n\n')
                    temporary, text = text[:cut], text[cut:]
                    try:
                        await message.answer(temporary, parse_mode='MarkdownV2')
                    except TelegramBadRequest:
                        logging.warning(str(TelegramBadRequest) + '||' + 'send_stream_text cut')
                        await message.answer(temporary, parse_mode='Markdown')
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
            logging.debug(temp_text)
            logging.info(f'TOTAL_TOKENS = {total_tokens} LENGTH = {total_len}')
    stop_event = asyncio.Event()
    try:
        await asyncio.gather(show_typing(bot, message.chat.id, stop_event, duration=60), send_stream_text(message))
    except ChatGoogleGenerativeAIError:
        logging.error(str(ChatGoogleGenerativeAIError))
        message.answer(str(ChatGoogleGenerativeAIError))
    except ValueError as e:
        logging.error(str(e.with_traceback(e.__traceback__)))
    finally:
        df.loc[message.from_user.id, 'history'] = str([store[message.from_user.id]])
        df.to_csv('users.csv')
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

async def set_main_menu(bot: Bot):

    main_menu_commands = [
        BotCommand(command='/help',
                   description='оказать помощь'),
        BotCommand(command='/stream',
                   description='генерация ответов ИИ'),
        BotCommand(command='/clear',
                   description='забыть историю сообщений')
    ]

    await bot.set_my_commands(main_menu_commands)

dp.callback_query.register(callback_help, F.data.in_(['stream', 'clear']))
dp.callback_query.register(callback_pets, F.data.in_(['fox', 'dog', 'cat']))
dp.message.register(answer_help, Command(commands=["help"]))
dp.message.register(change_stream, Command(commands=["stream"]))
dp.message.register(clear_history, Command(commands=["clear"]))
dp.message.register(change_model, Command(commands=["mini", "flash", "pro", "english"]))
dp.message.register(send_fox, Command(commands=["fox"]))
dp.message.register(send_cat, Command(commands=["cat"]))
dp.message.register(send_dog, Command(commands=["dog"]))
dp.message.register(answer_start, CommandStart())
dp.message.register(answer_langchain, F.content_type == ContentType.TEXT)
dp.message.register(send_photo, F.photo[-1].as_("mphoto"))  # F.content_type == 'photo' or F.photo or lambda m: m.photo
dp.message.register(send_sticker, lambda m: m.sticker)
dp.message.register(send_copy)
dp.my_chat_member.register(block, ChatMemberUpdatedFilter(KICKED))
dp.startup.register(set_main_menu)

if __name__ == "__main__":
    dp.run_polling(bot)