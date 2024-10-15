from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config
from .filters import ModelCallback as MC

models = config.models

def button(model: str, user_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=models[model], callback_data=MC(model=model, user_id=user_id).pack())

def keyboard_help(user_id: int, stream: bool, model: str) -> InlineKeyboardMarkup:
    """
    Returns a keyboard with buttons for streaming and clearing history.

    Args:
        stream: Если True - то вернет клавиатуру с "отключить" стриминг. Defaults to False.

    Returns:
        InlineKeyboardMarkup
    """

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text='🦊', callback_data='fox'),
        InlineKeyboardButton(text='🐈', callback_data='cat'),
        InlineKeyboardButton(text='🐶', callback_data='dog'))

    builder.row(
        *[b for b in [button('flash', user_id),
        button('english', user_id)] if  models[model] != b.text])
    if user_id in config.tg_bot.admin_ids:
        builder.row(
            *[b for b in [button('mini', user_id),
            button('pro', user_id),
            button('flux', user_id)] if  models[model] != b.text])

    builder.row(
        InlineKeyboardButton(text=['Включить стриминг ответов', 'Отключить стриминг ответов'][stream], callback_data='stream'),
        InlineKeyboardButton(text='Забыть историю сообщений', callback_data='clear'),
        width=1)

    return builder.as_markup()
