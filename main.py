import requests
import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, KICKED
from aiogram.types import Message, ChatMemberUpdated, BotCommand, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from src.filters import ModelCallback, available_model
from src.models import history_chat as hc, history_chat_stream as hcs
from src.model.flux import generate_flux_photo
from src.model.whisper import speach_to_text
from src.tools import convert_gemini_to_markdown as cgtm, lp, help_format
from src.keyboards import keyboard_help
from config import config


bot = Bot(config.tg_bot.token)
dp = Dispatcher()
models = config.models
users = config.users
users.load_from_db('test.db')

# Set up file handler for DEBUG and above
file_handler = logging.FileHandler('logs.log', 'w', 'utf-8', True)
file_handler.setLevel(logging.DEBUG)

# Set up stream handler for INFO and above
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Common formatter
formatter = logging.Formatter(
    '{asctime}|{levelname:7}|{filename}:{lineno}|{name}|{message}',
    style='{'
)
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, stream_handler])



def update_sql_parameter(id: int, parameter: str, value) -> None:
    """
    Updates a specific parameter for a user in the database.
    Args:
        id (int): The ID of the user whose parameter is to be updated.
        parameter (str): The name of the parameter/column to update.
        value: The new value to set for the specified parameter.
    Returns:
        None
    Raises:
        sqlite3.Error: If a database error occurs during the operation.
    """

    allowed_columns = {"stream", "model", "block", "eng_his", "oth_his"}  # Add valid column names here
    if parameter not in allowed_columns:
        raise ValueError(f"Invalid column name: {parameter}")

    connection = sqlite3.connect('test.db')
    try:
        cursor = connection.cursor()
        cursor.execute(f'UPDATE users SET {parameter} = ? WHERE id = ?', (value, id))
        connection.commit()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        raise
    finally:
        connection.close()

async def answer_start(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()

    user_id = message.from_user.id
    connection = sqlite3.connect('test.db')
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id, ))
        if not cursor.fetchone():
            cursor.execute("""INSERT INTO users (id, first_name, lang)
                            VALUES (?, ?, ?)""",
                    (user_id,
                    message.from_user.first_name,
                    message.from_user.language_code)
                    )
            users.add_user(user_id, lang=message.from_user.language_code)
        else:
            cursor.execute('UPDATE users SET block = 0 WHERE id = ?;', (user_id, ))
        connection.commit()
    finally:
        connection.close()

    logging.info(f"{user_id}, {message.from_user.first_name}, {message.from_user.language_code}")
    await message.answer(
        "*Приветствую!*\nЯ - бот с искусственным интеллектом.\nМогу помочь с изучением английского языка. Также могу служить помощником в различных задачах.\nДля дополнительной информации отправь - /help!", parse_mode='Markdown'
    )

async def answer_help(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()
    stream = users.stream(message.from_user.id)
    model = users.model(message.from_user.id)
    await message.answer(
        help_format(model, stream),
        reply_markup=keyboard_help(message.from_user.id, stream, model),
        parse_mode='Markdown'
    )

async def callback_help(query: CallbackQuery):
    user_id = query.message.chat.id
    model = users.model(user_id)

    if query.data == 'clear':
        await query.answer("История очищена.")
        if model == 'english':
            users.clear_english(user_id)
            update_sql_parameter(user_id, 'eng_his', '{"messages":[]}')
        else:
            users.clear_other(user_id)
            update_sql_parameter(user_id, 'oth_his', '{"messages":[]}')
    else:
        users.dict[user_id].stream = not users.stream(user_id)
        stream = users.stream(user_id)
        update_sql_parameter(user_id, 'stream', stream)
        await query.message.edit_text(
            help_format(model, stream),
            reply_markup=keyboard_help(user_id, stream, model),
            parse_mode='Markdown')

        await query.answer("Стриминг активирован.")

async def callback_model(query: CallbackQuery, callback_data: ModelCallback):
    user_id = query.message.chat.id

    #Checking if id in callback matches with id from query
    if callback_data.user_id == user_id:
        stream = users.stream(user_id)
        model = callback_data.model

        update_sql_parameter(user_id, 'model', model)
        users.dict[user_id].model = model

        await query.message.edit_text(
            help_format(model, stream),
            reply_markup=keyboard_help(user_id, stream, model),
            parse_mode='Markdown')

        await query.answer("Модель обновлена.")
    else:
        await query.answer("Error.")

async def change_stream(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()

    user_id = message.from_user.id
    users.dict[user_id].stream = not users.stream(user_id)
    stream = users.stream(user_id)
    update_sql_parameter(user_id, 'stream', stream)

    await message.answer(f"{'Режим стриминга сообщений для ответов ИИ активирован.'if stream else "Режим стриминга сообщений для ответов ИИ деактивирован."}")

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

async def clear_history(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()

    user_id = message.from_user.id
    model = users.model(user_id)

    if model == 'english':
        users.clear_english(user_id)
        update_sql_parameter(user_id, 'eng_his', '{"messages":[]}')
        await message.answer("История английского чата очищена.")
    else:
        users.clear_other(user_id)
        update_sql_parameter(user_id, 'oth_his', '{"messages":[]}')
        await message.answer("История всех чатов, кроме английского, очищена.")

async def send_ai_text(message: Message, my_question: str | None = None, voice_text: str = ''):

    if my_question:
        message_text = my_question
    else:
        message_text = message.text

    user_model = await available_model(message, bot)

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
    if not users.stream(message.from_user.id):
        basemessage = await hc(message, user_model, message_text)
        text = voice_text + basemessage.content
        ctext = cgtm(text)
        logging.debug(text)
        logging.debug(ctext)
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
        text = ""
        temp_text = ''
        response = await hcs(message, user_model, message_text)
        for chunk in response:
            if text:
                temp_text += chunk.content
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
                temp_text += voice_text + chunk.content
                voice_text = ""
                if '\n\n' in temp_text:
                    message_1 = await bot_send_message(message.chat.id, cgtm(temp_text))
                    text += temp_text
                    temp_text = ''  # Clear the buffer after updating
        if temp_text:   # Handle the last chunk
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

async def answer_langchain(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await send_ai_text(message)

    user_id = message.from_user.id
    if users.model(user_id) == 'english':
        update_sql_parameter(user_id, "eng_his", users.english(user_id).model_dump_json())
    else:
        update_sql_parameter(user_id, "oth_his", users.other(user_id).model_dump_json())

async def send_flux_photo(message: Message, my_question: str | None = None):

    task = asyncio.create_task(lp(bot, message.chat.id, cycles=36, action='upload_photo'))

    try:
        input_file = await generate_flux_photo(message, my_question)
        await bot.send_photo(chat_id=message.chat.id, photo=input_file, caption=my_question if my_question else None)
    except Exception as e:
        logging.error(e)
        await bot.send_message(chat_id=message.chat.id, text=f"An error occured: {e}")
    finally:
        task.cancel()

async def handle_voice(message: Message):
    try:
        user_id = message.from_user.id

        await bot.send_chat_action(message.chat.id, "typing" if users.model(user_id) != 'flux' else "upload_photo")

        text_from_voice = await speach_to_text(message, bot)

        if text_from_voice:
            if users.model(user_id) != 'flux':
                await send_ai_text(message, text_from_voice, voice_text=f">{text_from_voice.capitalize()}\n")
                if users.model(user_id) == 'english':
                    update_sql_parameter(user_id, 'eng_his', users.english(user_id).model_dump_json())
                else:
                    update_sql_parameter(user_id, 'oth_his', users.other(user_id).model_dump_json())
            else:
                await send_flux_photo(message, text_from_voice)
        else:
            await message.answer('An error occurred while extracting the text.')
    except Exception as e:
        await message.answer(f"Error handling voice message: {e}")

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
    update_sql_parameter(event.from_user.id, 'block', 1)
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
dp.message.register(answer_help, Command(commands=["help"]))#help
dp.message.register(change_stream, Command(commands=["stream"]))
dp.message.register(clear_history, Command(commands=["clear"]))
dp.message.register(answer_start, CommandStart())#start
dp.message.register(send_flux_photo, F.text, lambda m: users.model(m.from_user.id) == 'flux' )#flux_answer
dp.message.register(answer_langchain, F.text)#model_answer
dp.message.register(handle_voice, F.voice)
dp.message.register(send_sticker, lambda m: m.sticker)
dp.message.register(send_copy)
dp.my_chat_member.register(block, ChatMemberUpdatedFilter(KICKED))
dp.startup.register(set_main_menu)

if __name__ == "__main__":
    dp.run_polling(bot)