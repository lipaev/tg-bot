import requests
import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, KICKED
from aiogram.types import Message, ChatMemberUpdated, BotCommand, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from src.models import history_chat as hc, available_models
from src.tools import convert_gemini_to_markdown as cgtm, lp, generate_settings_text
from src.stt.whisper import speach_to_text
from src.filters import ModelCallback, TTSCallback, available_model
from src.keyboards import generate_inline_keyboard, additional_features
from config import config


dp = Dispatcher()
bot = config.bot
users = config.users
model_names = config.model_names
users.load_from_db('test/test.db')
logging = config.logging


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

    allowed_columns = {"stream", "temp", "model", "block", "eng_his", "oth_his"}  # Add valid column names here
    if parameter not in allowed_columns:
        raise ValueError(f"Invalid column name: {parameter}")

    connection = sqlite3.connect('test/test.db')
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
    connection = sqlite3.connect('test/test.db')
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
    except Exception as e:
        logging.error(e)
    finally:
        connection.close()

    logging.info(f"{user_id}, {message.from_user.first_name}, {message.from_user.language_code}")
    await message.answer(
        "*Приветствую!*\nЯ - бот с искусственным интеллектом.\nМогу помочь с изучением английского языка. Также могу служить помощником в различных задачах.\nДля дополнительной информации отправь - /help!", parse_mode='Markdown'
    )

async def display_user_settings(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()
    stream = users.stream(message.from_user.id)
    model = users.model(message.from_user.id)
    await message.answer(
        generate_settings_text(message.from_user.id),
        reply_markup=generate_inline_keyboard(message.from_user.id, stream, model),
        parse_mode='Markdown'
    )

async def handle_callback_settings(query: CallbackQuery):
    user_id = query.message.chat.id
    model = users.model(user_id)

    match query.data:
        case "stream":
            users.dict[user_id].stream = not users.stream(user_id)
            stream = users.stream(user_id)
            update_sql_parameter(user_id, 'stream', stream)
            await query.message.edit_text(
                generate_settings_text(user_id),
                reply_markup=generate_inline_keyboard(user_id, stream, model),
                parse_mode='Markdown')
            await query.answer("Стриминг " + ["деактивирован.", "активирован."][stream])
        case "clear":
            if not users.temp(user_id):
                if model == 'english':
                    users.english(user_id).clear()
                    update_sql_parameter(user_id, 'eng_his', '{"messages":[]}')
                    await query.answer("История английского чата очищена.")
                else:
                    users.other(user_id).clear()
                    update_sql_parameter(user_id, 'oth_his', '{"messages":[]}')
                    await query.answer("История прочего чата очищена.")
            else:
                users.temphis(user_id).clear()
                await query.answer("История временного чата очищена.")
        case "temp":
            users.dict[user_id].temp = not users.temp(user_id)
            temp = users.temp(user_id)
            stream = users.stream(user_id)
            update_sql_parameter(user_id, 'temp', temp)
            await query.message.edit_text(
                generate_settings_text(user_id),
                reply_markup=generate_inline_keyboard(user_id, stream, model),
                parse_mode='Markdown')
            await query.answer("Временный чат " + ["деактивирован.", "активирован."][temp])

async def callback_model(query: CallbackQuery, callback_data: ModelCallback):
    user_id = query.message.chat.id

    #Checking if id in callback matches with id from query
    if callback_data.user_id == user_id:
        stream = users.stream(user_id)
        model = callback_data.model

        update_sql_parameter(user_id, 'model', model)
        users.dict[user_id].model = model

        await query.message.edit_text(
            generate_settings_text(user_id),
            reply_markup=generate_inline_keyboard(user_id, stream, model),
            parse_mode='Markdown')

        await query.answer("Модель обновлена.")
    else:
        await query.answer("Error.")

async def callback_tts(query: CallbackQuery, callback_data: TTSCallback):

    user_id = query.from_user.id
    tts_model = callback_data.tts_model
    text = query.message.text

    if callback_data.user_id == user_id:
        tts_model = available_models['tts'].get(tts_model, None)
        if tts_model:
            await tts_model(query.message, text)
            await query.answer()
        else:
            await query.answer("Error. Model is not available.")
    else:
        await query.answer("Error.")

async def handle_commands(message: Message):
    if message.text.startswith(('/settings', '/help')):
        await display_user_settings(message)
    elif message.text.startswith('/temp'):
        await change_temp(message)
    elif message.text.startswith('/stream'):
        await change_stream(message)
    elif message.text.startswith('/clear'):
        await clear_history(message)
    elif message.text.startswith('/start'):
        await answer_start(message)

async def change_stream(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()

    user_id = message.from_user.id
    users.dict[user_id].stream = not users.stream(user_id)
    stream = users.stream(user_id)
    update_sql_parameter(user_id, 'stream', stream)

    await message.answer(f"{'Режим стриминга сообщений для ответов ИИ активирован.'if stream else "Режим стриминга сообщений для ответов ИИ деактивирован."}")

async def change_temp(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()

    user_id = message.from_user.id
    users.dict[user_id].temp = not users.temp(user_id)
    temp = users.temp(user_id)
    update_sql_parameter(user_id, 'temp', temp)

    await message.answer('Временный чат ' + ["деактивирован.", "активирован."][temp])

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

    if model in available_models['ttt']:
        if not users.temp(user_id):
            if model == 'english':
                users.english(user_id).clear()
                update_sql_parameter(user_id, 'eng_his', '{"messages":[]}')
                await message.answer("История английского чата очищена.")
            else:
                users.other(user_id).clear()
                update_sql_parameter(user_id, 'oth_his', '{"messages":[]}')
                await message.answer("История всех чатов, кроме английского, очищена.")
        else:
            users.temphis(user_id).clear()
            await message.answer("История временного чата очищена.")
    else:
        await message.answer(f"Модель {config.model_names[model]} не поддерживает историю чата.")

async def send_text(message: Message, voice_text: str | None = None):

    await bot.send_chat_action(message.chat.id, "typing")

    if voice_text:
        message_text = voice_text
    else:
        message_text = message.text

    quote = f">{voice_text.capitalize()}\n" if voice_text else ''
    user_model = await available_model(message)
    user_id = message.from_user.id
    disable_notification = False  # For reducing unnecesary notifications

    async def bot_send_message(chat_id: int, text: str, *, parse_mode='MarkdownV2', disable_notification=False):
        try:
            return await bot.send_message(
                chat_id,
                text,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
                reply_markup=additional_features(user_id))
        except TelegramBadRequest as e:
            if "can't parse entities" in str(e):
                logging.error(text)
                return await bot.send_message(
                    chat_id,
                    text,
                    disable_notification=disable_notification,
                    reply_markup=additional_features(user_id)
                    )
            logging.error(e)
            await message.answer(str(e))
        except Exception as e:
            logging.error(f"Error sending message: {e}")
    async def try_edit_message(message: Message, text: str, parse_mode='MarkdownV2'):
        try:
            await message.edit_text(
                text,
                parse_mode=parse_mode,
                reply_markup=additional_features(user_id)
                )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
            else:
                logging.error(text)
                logging.error(e)
                await message.answer(str(e))
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
    if not users.stream(message.from_user.id):
        basemessage = await hc(message, user_model, message_text, stream=False)
        text = quote + basemessage.content
        ctext = cgtm(text)
        logging.debug(text)
        logging.debug(ctext)
        while True:
            if len(ctext) <= 4096:
                message = await bot_send_message(
                    message.chat.id,
                    ctext,
                    disable_notification = disable_notification
                    )
                break
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
                await bot_send_message(
                    message.chat.id,
                    temporary,
                    disable_notification = disable_notification)
                disable_notification = True
    else:
        text = ""
        temp_text = ""
        response = await hc(message, user_model, message_text)
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
                        message_1 = await bot_send_message(
                            message.chat.id,
                            cgtm(text),
                            disable_notification = disable_notification)
                        disable_notification = True
            else:
                temp_text += quote + chunk.content
                quote = ""
                if '\n\n' in temp_text:
                    message_1 = await bot_send_message(
                        message.chat.id,
                        cgtm(temp_text),
                        disable_notification = disable_notification)
                    disable_notification = True
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
                    await bot_send_message(message.chat.id, cgtm(text), disable_notification=disable_notification)
            else:
                await bot_send_message(message.chat.id, cgtm(temp_text), disable_notification=disable_notification)
        logging.debug(text or temp_text + '\n' + '=' * 100)
        logging.debug(cgtm(text or temp_text))

    if not users.temp(user_id):
        if users.model(user_id) == 'english':
            update_sql_parameter(user_id, "eng_his", users.english(user_id).model_dump_json())
        else:
            update_sql_parameter(user_id, "oth_his", users.other(user_id).model_dump_json())

async def send_photo(message: Message, voice_text: str | None = None):

    user_model = users.model(message.from_user.id)
    if user_model != await available_model(message):
        return

    task = asyncio.create_task(lp(message.chat.id, cycles=26, action='upload_photo'))

    try:
        await available_models['tti'][user_model](message=message, voice_text=voice_text)
    except Exception as e:
        logging.error(e)
        await bot.send_message(chat_id=message.chat.id, text=f"An error occured: {e}")
    finally:
        task.cancel()

async def handle_voice(message: Message):
    try:
        user_model = users.model(message.from_user.id)
        if user_model != await available_model(message):
            return
        user_id = message.from_user.id

        await bot.send_chat_action(message.chat.id, "typing" if users.model(user_id) != 'flux' else "upload_photo")

        text_from_voice = await speach_to_text(message)

        if text_from_voice:
            if user_model not in available_models['tti']:
                await send_text(message, text_from_voice)
            else:
                await send_photo(message, text_from_voice)
        else:
            await message.answer('An error occurred while extracting the text.')
    except Exception as e:
        await message.answer('Error handling voice message.')
        logging.error(e)

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
        BotCommand(command='/settings',
                   description='показать настройки'),
        BotCommand(command='/temp',
                   description='переключить режим временного чата'),
        BotCommand(command='/stream',
                   description='переключить режим стриминга ответов ИИ'),
        BotCommand(command='/clear',
                   description='очистить историю сообщений')
    ]

    await bot.set_my_commands(main_menu_commands)

dp.callback_query.register(handle_callback_settings, F.data.in_(['stream', 'clear', 'temp']))
dp.callback_query.register(callback_model, ModelCallback.filter(F.model.in_(available_models['ttt'] | available_models['tti'])))
dp.callback_query.register(callback_tts, TTSCallback.filter(F.tts_model.in_(available_models['tts'])))
dp.callback_query.register(callback_pets, F.data.in_(['fox', 'dog', 'cat']))
dp.message.register(handle_commands, Command("settings", "help", "stream", "clear", "start", "temp"))
dp.message.register(send_photo, F.text, lambda m: users.model(m.from_user.id) in available_models['tti'] )
dp.message.register(send_text, F.text)#model_answer
dp.message.register(handle_voice, F.voice)
dp.message.register(send_sticker, lambda m: m.sticker)
dp.message.register(send_copy)
dp.my_chat_member.register(block, ChatMemberUpdatedFilter(KICKED))
dp.startup.register(set_main_menu)

if __name__ == "__main__":
    try:
        dp.run_polling(bot, close_bot_session=True)
    except Exception as e:
        logging.error(e)