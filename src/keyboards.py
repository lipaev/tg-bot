from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config
from .filters import ModelCallback as MC
from .models import available_models


def model_button(model: str, user_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=config.models[model], callback_data=MC(model=model, user_id=user_id).pack(), model=model)

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

    #models for anyone
    builder.row(*[button for button in [
            model_button('flash', user_id),
            model_button('english', user_id)
            ] if model != button.model and button.model in available_models])
    if user_id in config.tg_bot.admin_ids:
        #models for admins
        builder.row(*[button for button in [
                model_button('pro', user_id),
                model_button('flux', user_id),
                model_button('rag', user_id)
                ] if model != button.model and button.model in available_models])
        builder.adjust(3)

    builder.row(
        InlineKeyboardButton(text=['Включить стриминг ответов', 'Отключить стриминг ответов'][stream], callback_data='stream'),
        InlineKeyboardButton(text='Забыть историю сообщений', callback_data='clear'),
        width=1)

    return builder.as_markup()
