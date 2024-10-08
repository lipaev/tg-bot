from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def keyboard_help(stream: bool = False) -> InlineKeyboardMarkup:
    """
    Returns a keyboard with buttons for streaming and clearing history.

    Args:
        stream: Если True - то вернет клавиатуру с "отключить" стриминг. Defaults to False.

    Returns:
        InlineKeyboardMarkup
    """

    button_stream = InlineKeyboardButton(text=['Включить стриминг ответов ✅', 'Отключить стриминг ответов ❎'][stream],
                                         callback_data='stream')
    button_clear = InlineKeyboardButton(text='Забыть историю сообщений', callback_data='clear')

    button_fox = InlineKeyboardButton(text='🦊', callback_data='fox')
    button_cat = InlineKeyboardButton(text='🐈', callback_data='cat')
    button_dog = InlineKeyboardButton(text='🐶', callback_data='dog')

    keyboard_help = InlineKeyboardMarkup(inline_keyboard=[[button_fox, button_cat, button_dog], [button_stream], [button_clear]])

    return keyboard_help
