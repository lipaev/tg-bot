from aiogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config
from .filters import ModelCallback as MC

def keyboard_help(user_id: int, stream: bool, model: str) -> InlineKeyboardMarkup:
    """
    Returns a keyboard with buttons for streaming and clearing history.

    Args:
        stream: Если True - то вернет клавиатуру с "отключить" стриминг. Defaults to False.

    Returns:
        InlineKeyboardMarkup
    """

    models = config.models
    builder = InlineKeyboardBuilder()

    builder.row(
        IKB(text='🦊', callback_data='fox'),
        IKB(text='🐈', callback_data='cat'),
        IKB(text='🐶', callback_data='dog'))

    builder.row(
        *[b for b in [IKB(text=models['flash'], callback_data=MC(model='flash', user_id=user_id).pack()),
        IKB(text=models['english'], callback_data=MC(model='english', user_id=user_id).pack())] if  models[model] != b.text])
    if user_id in config.tg_bot.admin_ids:
        builder.row(
            *[b for b in [IKB(text=models['mini'], callback_data=MC(model='mini', user_id=user_id).pack()),
            IKB(text=models['pro'], callback_data=MC(model='pro', user_id=user_id).pack())] if  models[model] != b.text])

    builder.row(
        IKB(text=['Включить стриминг ответов', 'Отключить стриминг ответов'][stream], callback_data='stream'),
        IKB(text='Забыть историю сообщений', callback_data='clear'),
        width=1)

    return builder.as_markup()
