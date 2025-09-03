import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED
from aiogram.types import Message, ChatMemberUpdated, BotCommand

from commands import handle_commands, commands
from callbacks import *
from src.models import history_chat as hc, available_models
from src.tools import (
    convert_gemini_to_markdown as cgtm,
    lp,
    bot_send_message,
    try_edit_message
)
from src.filters import ModelCallback, TTSCallback, available_model
from src.keyboards import additional_features
from config import config
from src.users import update_user_data

dp = Dispatcher()
model_names = config.model_names
users.load_from_db()

async def send_text(message: Message, voice_message: Message | None = None):

    await bot.send_chat_action(message.chat.id, "typing")

    if voice_message:
        message_text = voice_message.text
    else:
        message_text = message.text

    #quote = f">{voice_message}\n" if voice_message else ''
    user_model = await available_model(message)
    user_id = message.from_user.id
    disable_notification = False  # For reducing unnecesary notifications

    try:
        if not users.stream(message.from_user.id):
            basemessage = await hc(message, user_model, message_text, stream=False)
            text = basemessage.content
            ctext = cgtm(text)
            logging.debug(text)
            logging.debug(ctext)
            while True:
                if len(ctext) <= 4096:
                    message = await bot_send_message(
                        message,
                        ctext,
                        disable_notification=disable_notification,
                        reply_markup_func=additional_features,
                        user_id=user_id
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
                        message,
                        temporary,
                        disable_notification=disable_notification,
                        user_id=user_id
                    )
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
                            await try_edit_message(message_1, ctext, additional_features, user_id=user_id)
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
                            await try_edit_message(message_1, cgtm(temporary), additional_features, user_id=user_id)
                            message_1 = await bot_send_message(
                                message,
                                cgtm(text),
                                reply_markup_func=additional_features,
                                disable_notification=disable_notification,
                                user_id=user_id
                            )
                            disable_notification = True
                else:
                    temp_text += chunk.content
                    # quote = ""
                    if '\n\n' in temp_text:
                        message_1 = await bot_send_message(
                            message,
                            cgtm(temp_text),
                            reply_markup_func=additional_features,
                            disable_notification=disable_notification,
                            user_id=user_id
                        )
                        disable_notification = True
                        text += temp_text
                        temp_text = ''  # Clear the buffer after updating
            if temp_text:   # Handle the last chunk
                if text:
                    text += temp_text
                    ctext = cgtm(text)
                    if len(ctext) <= 4096:
                        await try_edit_message(message_1, ctext, additional_features, user_id=user_id)
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
                        await try_edit_message(message_1, cgtm(temporary), additional_features, user_id=user_id)
                        await bot_send_message(
                            message,
                            cgtm(text),
                            reply_markup_func=additional_features,
                            disable_notification=disable_notification,
                            user_id=user_id
                        )
                else:
                    await bot_send_message(
                        message,
                        cgtm(temp_text),
                        reply_markup_func=additional_features,
                        disable_notification=disable_notification,
                        user_id=user_id
                    )
            logging.debug(text or temp_text + '\n' + '=' * 100)
            logging.debug(cgtm(text or temp_text))
    except Exception as e:
        logging.error(e)
        if "No generation chunks were returned" in str(e):
            await bot.send_message(chat_id=message.chat.id, text="No response from the model. Perhaps you exceeded your quota. Try again later or change the model.")
        else:
            await bot.send_message(chat_id=message.chat.id, text="An error occured while generating a response.")

    if not users.temp(user_id):
        if users.model(user_id) == 'english':
            await update_user_data(user_id, "eng_his", users.english(user_id).model_dump_json(), config.sqlconninfo)
        else:
            await update_user_data(user_id, "oth_his", users.other(user_id).model_dump_json(), config.sqlconninfo)

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
    # try:
    user_model = users.model(message.from_user.id)
    if user_model != await available_model(message):
        return
    user_id = message.from_user.id

    await bot.send_chat_action(message.chat.id, "typing" if users.model(user_id) != 'flux' else "upload_photo")

    text_from_voice = await available_models['stt']['faster-whisper'](message.voice.file_id)

    if text_from_voice:
        if user_model not in available_models['tti']:
            voice_message = await bot_send_message(
                message,
                cgtm(f">{text_from_voice}"),
                additional_features,
                disable_notification=True,
                user_id=user_id
                )
            await send_text(message, voice_message)
        else:
            await send_photo(message, text_from_voice)
    else:
        await message.answer('An error occurred while extracting the text.')
    # except Exception as e:
    #     await message.answer('Error handling voice message.')
    #     logging.error(e)

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
    await update_user_data(event.from_user.id, 'block', 1, config.sqlconninfo)
    print(event.from_user.id, event.from_user.first_name, "blocked the bot")

async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command='/info',
                   description='Настройки'),
        BotCommand(command='/history',
                   description='История чата'),
        BotCommand(command='/clear',
                   description='Очистить историю сообщений'),
        BotCommand(command='/temp',
                   description='Переключить режим временного чата'),
        BotCommand(command='/stream',
                   description='Переключить режим стриминга ответов ИИ'),
    ]
    await bot.set_my_commands(main_menu_commands)

dp.callback_query.register(handle_callback_settings, F.data.in_(['stream', 'clear', 'temp']))
dp.callback_query.register(callback_model, ModelCallback.filter(F.model.in_(available_models['ttt'] | available_models['tti'])))
dp.callback_query.register(callback_tts, TTSCallback.filter(F.tts_model.in_(available_models['tts'])))
dp.callback_query.register(callback_pets, F.data.in_(['fox', 'dog', 'cat']))
import re
dp.message.register(handle_commands, Command(*commands, re.compile(r"del_(\d+)"), re.compile(r"show_(\d+)")))
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