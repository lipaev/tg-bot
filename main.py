import requests
import asyncio
import logging
import pandas as pd

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, KICKED
from aiogram.types import Message, ContentType, ChatMemberUpdated, PhotoSize, BotCommand, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk # For eval()

from mylibr.filters import WritingOnFile, ModelCallback
from mylibr.aicom import history_chat as hc, history_chat_stream as hcs, store, InMemoryHistory, bytes_photo_flux
from mylibr.features import convert_gemini_to_markdown as cgtm, show_typing
from mylibr.keyboards import keyboard_help
from config import config
from vcb import help_format


bot = Bot(config.tg_bot.token)
dp = Dispatcher()
df = pd.read_csv('users.csv', index_col='id')
models = config.models
store.update(dict(zip(df.index, map(lambda x: eval(x)[0], df['history'].to_dict().values()))))
handler = logging.FileHandler('logs.log', mode='w', encoding='utf-8')
handler.addFilter(WritingOnFile())
logging.basicConfig(level=logging.DEBUG,
                    format='{asctime}|{levelname:7}|{filename}:{lineno}|{name}||{message}',
                    style='{',
                    handlers=[handler, logging.StreamHandler()])


async def answer_start(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()
    df.loc[message.from_user.id] = [message.from_user.first_name,
                                    0,
                                    False,
                                    'english',
                                    message.from_user.language_code,
                                    str([InMemoryHistory()])]
    df.to_csv('users.csv')
    logging.info(f"{message.from_user.id}, {message.from_user.first_name}, {message.from_user.language_code}")
    await message.answer(
        "*Приветствую!*\nЯ - бот с искусственным интеллектом.\nМогу *помочь* с изучением английского языка. Также могу *служить* помощником в различных задачах.\nДля дополнительной информации отправь - /help!", parse_mode='Markdown'
    )

async def answer_help(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()
    stream = df.stream[message.from_user.id]
    await message.answer(
        help_format(df.model[message.from_user.id], stream),
        reply_markup=keyboard_help(message.from_user.id, stream, df.model[message.from_user.id]),
        parse_mode='Markdown'
    )

async def callback_help(query: CallbackQuery):
    user_id = query.message.chat.id
    if query.data == 'clear':
        store[user_id] = InMemoryHistory()
        await query.answer("История очищена.")
        df.loc[user_id, 'history'] = str([InMemoryHistory()])
        df.to_csv('users.csv')
    else:
        df.loc[user_id, 'stream'] = not df.loc[user_id, 'stream']
        df.to_csv('users.csv')
        stream = df.loc[user_id, 'stream']
        await query.message.edit_text(
            help_format(df.model[user_id], stream),
            reply_markup=keyboard_help(user_id, stream, df.model[user_id]),
            parse_mode='Markdown')
        await query.answer("Стриминг активирован.")

async def callback_model(query: CallbackQuery, callback_data: ModelCallback):

    if callback_data.user_id == query.message.chat.id:
        stream = df.loc[query.message.chat.id, 'stream']
        model = callback_data.model
        await query.message.edit_text(
            help_format(model, stream),
            reply_markup=keyboard_help(query.message.chat.id, stream, model),
            parse_mode='Markdown')
        await query.answer("Модель обновлена.")
        df.loc[query.message.chat.id, 'model'] = model
        df.to_csv('users.csv')
    else:
        await query.answer("Error.")

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

    async def bot_send_message(chat_id: int, text: str, parse_mode='MarkdownV2'):
                try:
                    return await bot.send_message(chat_id, text, parse_mode=parse_mode)
                except TelegramBadRequest as e:
                    if "can't parse entities" in str(e):
                        logging.error(text)
                        return await bot.send_message(chat_id, text)
                    logging.error(e)
                except Exception as e:
                    logging.error(f"Error sending message: {str(e)}")
    async def try_edit_message(message: Message, text: str, parse_mode='MarkdownV2'):
                try:
                    await message.edit_text(text, parse_mode=parse_mode)
                except TelegramBadRequest as e:
                    if "message is not modified" in str(e):
                        pass
                    else:
                        logging.error(text)
                        logging.error(e)
                except Exception as e:
                    logging.error(f"Error sending message: {str(e)}")
    async def send_stream_text(message: Message):
        if not df.stream[message.from_user.id]: #  or df.loc[message.from_user.id, 'model'] == 'mini'
            basemessage = await hc(message, df.loc[message.from_user.id].model)
            text = basemessage.content
            ctext = cgtm(text)
            print('*' * 100)
            logging.debug(text)
            logging.debug(ctext)
            #logging.info(f'TOTAL_TOKENS={basemessage.usage_metadata['total_tokens']} LENGTH={len(ctext)}')
            start = True
            while start:
                if len(ctext) <= 4096:
                    start = False
                    await bot_send_message(message.chat.id, ctext)
                else:
                    count = ctext[0:4096].count('```')
                    code = ctext[0:4096].rfind('```')
                    cut = ctext[0:4096].rfind('\n\n')
                    if count % 2 == 0 and count > 0:
                        if code > cut:
                            cut = code + 3
                    elif count > 0:
                        cut = code
                    elif cut == -1:
                        cut = ctext.rfind('\n', 0, 4096)
                    else:
                        cut = ctext.rfind(' ', 0, 4096)
                    temporary, ctext = ctext[:cut], ctext[cut:]
                    await bot_send_message(message.chat.id, temporary)
        else:
            text = ''
            temp_text = ''
            total_tokens = 0
            total_len = 0
            response = await hcs(message, df.loc[message.from_user.id].model)
            for chunk in response:
                if text:
                    temp_text += chunk.content
                    #total_len += len(chunk.content)
                    #total_tokens += chunk.usage_metadata['output_tokens']
                    if '\n\n' in temp_text:
                        text += temp_text
                        ctext = cgtm(text)
                        temp_text = ''
                        if len(ctext) <= 4096:
                            await try_edit_message(message_1, ctext)
                        else:
                            count = text[0:4096].count('```')
                            code = text[0:4096].rfind('```')
                            cut = text[0:4096].rfind('\n\n')
                            if count % 2 == 0 and count > 0:
                                if code > cut:
                                    cut = code + 3
                            elif count > 0:
                                cut = code
                            elif cut == -1:
                                cut = text.rfind('\n', 0, 4096)
                            else:
                                cut = text.rfind(' ', 0, 4096)
                            temporary, text = text[:cut], text[cut:]
                            await try_edit_message(message_1, cgtm(temporary))
                            message_1 = await bot_send_message(message.chat.id, cgtm(text))
                else:
                    temp_text += chunk.content
                    #total_len += len(chunk.content)
                    #total_tokens += chunk.usage_metadata['output_tokens']
                    if '\n\n' in temp_text:
                        message_1 = await bot_send_message(message.chat.id, cgtm(temp_text))
                        text += temp_text
                        temp_text = ''  # Clear the buffer after updating
            if temp_text:
                if text:
                    text += temp_text
                    ctext = cgtm(text)
                    if len(ctext) <= 4096:
                        await try_edit_message(message_1, ctext)
                    else:
                        count = text[0:4096].count('```')
                        code = text[0:4096].rfind('```')
                        cut = text[0:4096].rfind('\n\n')
                        if count % 2 == 0 and count > 0:
                            if code > cut:
                                cut = code + 3
                        elif count > 0:
                            cut = code
                        elif cut == -1:
                            cut = text.rfind('\n', 0, 4096)
                        else:
                            cut = text.rfind(' ', 0, 4096)
                        temporary, text = text[:cut], text[cut:]
                        await try_edit_message(message_1, cgtm(temporary))
                        await bot_send_message(message.chat.id, cgtm(text))
                else:
                    await bot_send_message(message.chat.id, cgtm(temp_text))
            logging.debug(text or temp_text + '\n' + '=' * 100)
            logging.debug(cgtm(text or temp_text))
            #logging.info(f'TOTAL_TOKENS = {total_tokens + chunk.usage_metadata['input_tokens']} LENGTH = {total_len}')

    await send_stream_text(message)
    df.loc[message.from_user.id, 'history'] = str([store[message.from_user.id]])
    df.to_csv('users.csv')

async def send_flux_photo(message: Message):

    m = await bot.send_message(message.chat.id, "Изображение генерируется...")
    await bytes_photo_flux(message)
    await m.delete()

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
dp.callback_query.register(callback_model, ModelCallback.filter(F.model.in_(models)))
dp.callback_query.register(callback_pets, F.data.in_(['fox', 'dog', 'cat']))
dp.message.register(answer_help, Command(commands=["help"]))
dp.message.register(change_stream, Command(commands=["stream"]))
dp.message.register(clear_history, Command(commands=["clear"]))
dp.message.register(change_model, Command(commands=["mini", "flash", "pro", "english", "flux"]))
dp.message.register(answer_start, CommandStart())
dp.message.register(send_flux_photo, F.content_type == ContentType.TEXT, lambda m: df.model[m.from_user.id] == 'flux' )
dp.message.register(answer_langchain, F.content_type == ContentType.TEXT)
#dp.message.register(send_photo, F.photo[-1].as_("mphoto"))  # F.content_type == 'photo' or F.photo or lambda m: m.photo
dp.message.register(send_sticker, lambda m: m.sticker)
dp.message.register(send_copy)
dp.my_chat_member.register(block, ChatMemberUpdatedFilter(KICKED))
dp.startup.register(set_main_menu)

if __name__ == "__main__":
    dp.run_polling(bot)