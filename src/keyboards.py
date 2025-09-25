from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config
from .filters import ModelCallback, TTSCallback
from .models import available_models


def generate_inline_keyboard(user_id: int, stream: bool, model: str) -> InlineKeyboardMarkup:
    """
    Returns a keyboard with buttons for streaming and clearing history.

    Args:
        stream: Если True - то вернет клавиатуру с "отключить" стриминг. Defaults to False.

    Returns:
        InlineKeyboardMarkup
    """

    def model_button(model: str, user_id: int) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=config.model_names.get(model, model),
            callback_data=ModelCallback(model=model, user_id=user_id).pack(),
            model=model
            )

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text='🦊', callback_data='fox'),
        InlineKeyboardButton(text='🐈', callback_data='cat'),
        InlineKeyboardButton(text='🐶', callback_data='dog'))

    buttons_for_anyone = [
        model_button('flash_2.0', user_id),
        model_button('flash_2.5_lite', user_id),
        model_button('english', user_id),
        model_button("gemini-flash-image", user_id)
    ]

    buttons_for_admins = [
        model_button('flash', user_id),
        model_button('pro', user_id),
        model_button('flux', user_id),
        model_button('rag', user_id)
    ]

    builder.row(*[
        button for button in buttons_for_anyone
        if model != button.model and button.model in available_models['ttt'] | available_models['tti']
    ], width=2)

    if user_id in config.admin_ids:
        builder.row(*[
            button for button in buttons_for_admins
            if model != button.model and button.model in available_models['ttt'] | available_models['tti']
        ], width=2)

    if config.users.temp(user_id):
        temp_chat = 'Отключить временный чат✍️'
        clear_text = 'Очистить историю временного чата🌪'
    else:
        temp_chat = 'Включить временный чат⏳'
        clear_text = ['Очистить историю прочего чата🧻', 'Очистить историю английского чата🗑'][model == 'english']
    stream_text = ['Включить стриминг ответов🏃‍♂️', 'Отключить стриминг ответов🧎‍♂️'][stream]

    buttons = [
        InlineKeyboardButton(text=temp_chat, callback_data='temp'),
        InlineKeyboardButton(text=stream_text, callback_data='stream'),
        InlineKeyboardButton(text=clear_text, callback_data='clear'),
        InlineKeyboardButton(text="Показать историю сообщений.", callback_data='history'),
        InlineKeyboardButton(text="Убрать сообщение", callback_data='delete'),
        ]

    builder.row(*[
            button for button in buttons
            if not (button.callback_data == 'clear' and model not in available_models['ttt']) #Cheking whether the model supports a clearing history.
        ], width=1)

    return builder.as_markup()

def additional_keyboard(user_id: int) -> InlineKeyboardMarkup:
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

    builder.row(
        *[tts_button(alias, user_id) for alias in available_models['tts']],
        InlineKeyboardButton(text="Убрать сообщение", callback_data="delete"),
        width=4
        )

    return builder.as_markup()
