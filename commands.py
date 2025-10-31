import psycopg
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import config
from src.users import update_user_data
from src.models import available_models
from src.keyboards import generate_inline_keyboard, additional_keyboard
from src.tools import convert_gemini_to_markdown as cgtm, send_any_text
from langchain_google_genai import GoogleGenerativeAI

genai_model = GoogleGenerativeAI(model="gemini-flash-lite-latest")
logging = config.logging
users = config.users
bot = config.bot

async def handle_commands(message: Message):
    for command in commands:
        if message.text.startswith('/' + command):
            await commands[command](message)
            return True

async def show_history(message: Message, *, edit_message_id: int=0, quser_id: int | None=None):
    """
    Shows a message history.

    Args:
        message: aiogram message object.
        edit_message_id: The last showing history message id. Defaults to 0.
        quser_id: The user id from a CallbackQuery. Defaults to None.
    """
    user_id = quser_id or message.from_user.id

    messages = users.get_user_history(user_id).messages
    text = []
    len_mess = len(messages)
    if not len_mess:
        await message.answer('History is empty.')
        return
    max_length = 4096 // len_mess
    logging.info(f"Max_length: {max_length}")
    available_characters = 0
    full_length = 0
    raw_length = 0
    for n, m in enumerate(messages, 1):
        six = 0
        mtext = m.text()
        postfix = ""
        if m.type != 'human':
            postfix = f'/del\_{n//2}  /show\_{n//2}\n\n'
            emoji = '🤖'
        else:
            emoji = '👶'
        template_text = "**>{}{}||\n" + postfix
        convertedMtext = cgtm(mtext, expandable=True)
        len_convertedMtext = len(convertedMtext)
        len_templateText = len(template_text)
        if len_convertedMtext + len_templateText - 3 > max_length:
            # 3 - скобки и эмодзи в шаблоне 6 - экранированные точки в конце
            six = 6
            logging.debug(
                template_text.format(emoji, mtext[:max_length - len_templateText + 3 - six + available_characters] + '...')
                )
            convertedMtext = cgtm(
                mtext[:max_length - len_templateText + 3 - 6 + available_characters] + '...',
                expandable=True
                )
            available_characters = 0
        else:
            available_characters += max_length - (len_convertedMtext + len_templateText - 3)
            logging.debug(template_text.format(emoji, mtext))
        result = template_text.format(emoji, convertedMtext)
        raw_length += len(template_text) - 3 + len(emoji) + len(convertedMtext) - six
        full_length += len(result)
        logging.info(
            f"Result_{n}: {len(result)} ".ljust(15) + \
            f"Available_chars: {available_characters} ".ljust(22) + \
            f"Full: {full_length} ".ljust(10) + \
            f"Raw: {raw_length}".ljust(9)
            )
        text.append(result)

    text = ''.join(text).strip(" >\n")
    if text:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="Убрать сообщение",
                callback_data="delete"
            )]])
        if edit_message_id:
            await bot.edit_message_text(
                text,
                chat_id=message.chat.id,
                message_id=edit_message_id,
                parse_mode='MarkdownV2',
                reply_markup=keyboard
            )
        else:
            logging.debug(text)
            if not quser_id:
                await message.delete()
            message = await message.answer(text, parse_mode='MarkdownV2', reply_markup=keyboard)
            users.dict[user_id].last_sh_his_id = message.message_id
    else:
        if edit_message_id:
            await bot.delete_message(chat_id=message.chat.id, message_id=edit_message_id)
        await message.answer('History is empty.')

async def clear_history(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()

    user_id = message.from_user.id
    model = users.model(user_id)

    if model in available_models['ttt']:
        if not users.temp(user_id):
            if model == 'english':
                users.english(user_id).clear()
                await update_user_data(user_id, 'eng_his', '{"messages":[]}', config.sqlconninfo)
                await message.answer("История английского чата очищена.")
            else:
                users.other(user_id).clear()
                await update_user_data(user_id, 'oth_his', '{"messages":[]}', config.sqlconninfo)
                await message.answer("История всех чатов, кроме английского, очищена.")
        else:
            users.temphis(user_id).clear()
            await message.answer("История временного чата очищена.")
    else:
        await message.answer(f"Модель {config.model_names[model]} не поддерживает историю чата.")

async def display_info(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")

    def generate_settings_text(user_id: int):
        users = config.users
        l = ['❎', '✅']
        text = (
            f"Ваша модель: {config.model_names[users.model(user_id)]}\n"
            f"Стриминг ответов ИИ: {l[users.stream(user_id)]}\n"
            f"Временный чат: {l[users.temp(user_id)]}"
            )
        return text

    stream = users.stream(message.from_user.id)
    model = users.model(message.from_user.id)
    await message.answer(
        generate_settings_text(message.from_user.id),
        reply_markup=generate_inline_keyboard(message.from_user.id, stream, model),
        parse_mode='Markdown'
    )

async def answer_start(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id
    with psycopg.connect(config.sqlconninfo, autocommit=True) as aconn:
        with aconn.cursor() as cur:
            cur.execute('SELECT id FROM users WHERE id = %s', (user_id, ))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO users (id, first_name, lang) VALUES (%s, %s, %s)",
                    (user_id,
                    message.from_user.first_name,
                    message.from_user.language_code)
                    )
                users.add_user(user_id, lang=message.from_user.language_code)
            else:
                cur.execute('UPDATE users SET block = false WHERE id = %s;', (user_id, ))

    logging.info(f"{user_id}, {message.from_user.first_name}, {message.from_user.language_code}")
    await message.answer(
        "*Приветствую!*\nЯ - бот с искусственным интеллектом.\nМогу помочь с изучением английского языка."
        " Также могу служить помощником в различных задачах.\nДля дополнительной информации отправь - /info!",
        parse_mode='Markdown'
    )

async def change_stream(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()

    user_id = message.from_user.id
    users.dict[user_id].stream = not users.stream(user_id)
    stream = users.stream(user_id)
    await update_user_data(user_id, 'stream', stream, config.sqlconninfo)

    await message.answer(f"{'Режим стриминга сообщений для ответов ИИ активирован.'if stream else "Режим стриминга сообщений для ответов ИИ деактивирован."}")

async def change_temp(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await message.delete()

    user_id = message.from_user.id
    users.dict[user_id].temp = not users.temp(user_id)
    temp = users.temp(user_id)
    await update_user_data(user_id, 'temp', temp, config.sqlconninfo)

    await message.answer('Временный чат ' + ["деактивирован.", "активирован."][temp])

async def delete_message(message: Message):
    user_id = message.from_user.id
    pair_number = 2 * int(message.text.lstrip('/del_show'))

    messages = config.users.get_user_history(user_id).messages
    if pair_number <= len(messages):
        del config.users.get_user_history(user_id).messages[pair_number-2:pair_number]

        if not users.temp(user_id):
            if users.model(user_id) == 'english':
                await update_user_data(user_id, "eng_his", users.english(user_id).model_dump_json(), config.sqlconninfo)
            else:
                await update_user_data(user_id, "oth_his", users.other(user_id).model_dump_json(), config.sqlconninfo)

        await message.delete()
        await show_history(message, edit_message_id=users.last_sh_his_id(user_id))
        if not users.temp(user_id):
            if users.model(user_id) == 'english':
                await update_user_data(user_id, "eng_his", users.english(user_id).model_dump_json(), config.sqlconninfo)
            else:
                await update_user_data(user_id, "oth_his", users.other(user_id).model_dump_json(), config.sqlconninfo)
    else:
        await message.answer(f"Message pair №{pair_number//2} are not exist.")

async def show_message_pair(message: Message):
    user_id = message.from_user.id
    pair_number = 2 * int(message.text.lstrip('/del_show'))
    messages = config.users.get_user_history(user_id).messages
    if pair_number <= len(messages):
        text = f">{messages[pair_number-2].content}\n{messages[pair_number-1].content}"
        await send_any_text(
            message,
            text=text,
            convert=True,
            user_id=user_id,
            keyboard=additional_keyboard
            )
    else:
        await message.answer(f"Message pair №{pair_number//2} are not exist.")

async def translate(message: Message):
    textToTranslate = message.text[4:]
    if textToTranslate:
        response = await genai_model.ainvoke(
                f"Переведи на русский язык «{textToTranslate}»"
                )
        await send_any_text(
            message,
            text=response,
            convert=True,
            user_id=message.from_user.id,
            keyboard=additional_keyboard
        )
    else:
        response = "Напишите текст для перевода после `/tr`\. Например: `/tr your text`\."
        await message.answer(
            response,
            parse_mode="MarkdownV2",
            reply_markup=additional_keyboard(message.from_user.id),
        )
    await message.delete()

async def to_voice(message: Message):
    textToVoice = message.text[4:]
    if textToVoice:
        await available_models["tts"]["ava_bing"](message, textToVoice)
    else:
        response = "Напишите текст для озвучивания после `/vc`\. Например: `/vc your text`\."
        await message.answer(
            response,
            parse_mode="MarkdownV2",
            reply_markup=additional_keyboard(message.from_user.id),
        )

commands = {
    'info': display_info,
    'temp': change_temp,
    'stream': change_stream,
    'clear': clear_history,
    'start': answer_start,
    'history': show_history,
    'del_': delete_message,
    'show_': show_message_pair,
    "tr": translate,
    "vc": to_voice
}