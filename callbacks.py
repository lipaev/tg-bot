import requests
from src.models import available_models
from config import config
from src.users import update_user_data
from src.keyboards import generate_inline_keyboard
from aiogram.types import CallbackQuery
from src.filters import ModelCallback, TTSCallback
from src.tools import generate_settings_text

logging = config.logging
users = config.users
bot = config.bot

async def handle_callback_settings(query: CallbackQuery):
    user_id = query.message.chat.id
    model = users.model(user_id)

    match query.data:
        case "stream":
            users.dict[user_id].stream = not users.stream(user_id)
            stream = users.stream(user_id)
            await update_user_data(user_id, 'stream', stream, config.sqlconninfo)
            await query.message.edit_text(
                generate_settings_text(user_id),
                reply_markup=generate_inline_keyboard(user_id, stream, model),
                parse_mode='Markdown')
            await query.answer("Стриминг " + ["деактивирован.", "активирован."][stream])
        case "clear":
            if not users.temp(user_id):
                if model == 'english':
                    users.english(user_id).clear()
                    await update_user_data(user_id, 'eng_his', '{"messages":[]}', config.sqlconninfo)
                    await query.answer("История английского чата очищена.")
                else:
                    users.other(user_id).clear()
                    await update_user_data(user_id, 'oth_his', '{"messages":[]}', config.sqlconninfo)
                    await query.answer("История прочего чата очищена.")
            else:
                users.temphis(user_id).clear()
                await query.answer("История временного чата очищена.")
        case "temp":
            users.dict[user_id].temp = not users.temp(user_id)
            temp = users.temp(user_id)
            stream = users.stream(user_id)
            await update_user_data(user_id, 'temp', temp, config.sqlconninfo)
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

        await update_user_data(user_id, 'model', model, config.sqlconninfo)
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
