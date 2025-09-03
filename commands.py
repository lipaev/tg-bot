from aiogram.types import Message
from src.models import available_models
from config import config
from src.users import update_user_data
from src.keyboards import generate_inline_keyboard
from src.tools import convert_gemini_to_markdown as cgtm
import psycopg

logging = config.logging
users = config.users
bot = config.bot

async def handle_commands(message: Message):
    for command in commands:
        if message.text.startswith('/' + command):
            await commands[command](message)
            return True

async def show_history(message: Message, edit_message_id: int | None=None):
    user_id = message.from_user.id

    messages = users.get_user_history(user_id).messages
    text = []
    for n, m in enumerate(messages, 1):
        mtext = m.text().split()
        if len(mtext) > 8:
            mtext = ' '.join(mtext[:8]) + '...'
        else:
            mtext = ' '.join(mtext)
        postfix = ""
        if m.type != 'human':
            postfix = f'/del_{n//2}  /show_{n//2}\n'
        text.append(f"{m.type[:2].upper()}: {mtext}\n{postfix}")

    text = ''.join(text)
    if text:
        if edit_message_id and edit_message_id != 0:
            await bot.edit_message_text(text, chat_id=message.chat.id, message_id=edit_message_id)
        else:
            message = await message.answer(text)
            users.dict[user_id].last_sh_his_id = message.message_id
    else:
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
        del messages[pair_number-2:pair_number]
        await message.delete()
        await show_history(message, users.last_sh_his_id(user_id))
        if not users.temp(user_id):
            if users.model(user_id) == 'english':
                await update_user_data(user_id, "eng_his", users.english(user_id).model_dump_json(), config.sqlconninfo)
            else:
                await update_user_data(user_id, "oth_his", users.other(user_id).model_dump_json(), config.sqlconninfo)
    else:
        await message.answer(f"Message pair {pair_number//2} are not exist.")

async def show_message(message: Message):
    user_id = message.from_user.id
    pair_number = 2 * int(message.text.lstrip('/del_show'))

    messages = config.users.get_user_history(user_id).messages
    if pair_number <= len(messages):
        await message.delete()
        await message.answer(cgtm(f">{messages[pair_number-2].content}\n{messages[pair_number-1].content}"), parse_mode="MarkdownV2")
    else:
        await message.answer(f"Message pair {pair_number//2} are not exist.")

commands = {
    'info': display_info,
    'temp': change_temp,
    'stream': change_stream,
    'clear': clear_history,
    'start': answer_start,
    'history': show_history,
    'del_': delete_message,
    'show_': show_message
}