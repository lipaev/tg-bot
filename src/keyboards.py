from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config
from .filters import ModelCallback, TTSCallback
from .models import available_models


def keyboard_help(user_id: int, stream: bool, model: str) -> InlineKeyboardMarkup:
    """
    Returns a keyboard with buttons for streaming and clearing history.

    Args:
        stream: Если True - то вернет клавиатуру с "отключить" стриминг. Defaults to False.

    Returns:
        InlineKeyboardMarkup
    """

    def model_button(model: str, user_id: int) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=config.model_names[model],
            callback_data=ModelCallback(model=model, user_id=user_id).pack(),
            model=model
            )

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text='🦊', callback_data='fox'),
        InlineKeyboardButton(text='🐈', callback_data='cat'),
        InlineKeyboardButton(text='🐶', callback_data='dog'))

    buttons_for_anyone = [
        model_button('flash', user_id),
        model_button('english', user_id),
        model_button("gemini-flash-image", user_id)
    ]

    buttons_for_admins = [
        model_button('pro', user_id),
        model_button('flux', user_id),
        model_button('rag', user_id)
    ]

    builder.row(*[
        button for button in buttons_for_anyone
        if model != button.model and button.model in available_models['ttt'] | available_models['tti']
    ])

    if user_id in config.admin_ids:
        builder.row(*[
            button for button in buttons_for_admins
            if model != button.model and button.model in available_models['ttt'] | available_models['tti']
        ])

        builder.adjust(3)

    builder.row(
        InlineKeyboardButton(text=['Включить стриминг ответов', 'Отключить стриминг ответов'][stream], callback_data='stream'),
        InlineKeyboardButton(text='Забыть историю сообщений', callback_data='clear'),
        width=1)

    return builder.as_markup()

def additional_features(user_id: int, text: str) -> InlineKeyboardMarkup:
    """
    Returns a keyboard with buttons that extend an interaction with messages.

    Args:
        text: The text that will be sent in callback.

    Returns:
        InlineKeyboardMarkup
    """

    def tts_button(tts_model: str, user_id: int) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=config.model_names[tts_model],
            callback_data=TTSCallback(
                tts_model=tts_model,
                user_id=user_id
                ).pack()
            )

    builder = InlineKeyboardBuilder()

    builder.row(*[tts_button(alias, user_id) for alias in available_models['tts']])

    return builder.as_markup()
