from typing import Iterator
from aiogram.types import Message
from langchain_core.messages import BaseMessage, BaseMessageChunk
from .tools import decode_language_code as dlc
from config import config

#from .model.pro import chain_pro_history
from .model.flash import chain_flash_history
from .model.english import chain_english_history
from .model.flux import generate_flux_photo

users = config.users
available_models = {'flash': chain_flash_history,
          #'pro': chain_pro_history,
          'english': chain_english_history,
          'flux': generate_flux_photo}

async def history_chat(message: Message, chain: str, my_question: str | None = None) -> BaseMessage:
    """Asyncсhronous chat with history"""

    message_text = my_question or message.text
    user_id = message.from_user.id
    lang_group = 'eng' if chain == 'english' else 'oth'

    if len(users.get_user_history(user_id, lang_group).messages) > 44:
        del users.get_user_history(user_id, lang_group).messages[:2]
        print(len(users.get_user_history(user_id, lang_group).messages))

    if message.quote:
        question = f"«{message.quote.text}»\n{message_text}"
    elif message.reply_to_message:
        question = f"«{message.reply_to_message.text}»\n{message_text}"
    else:
        question = message_text

    return available_models[chain].invoke(  # noqa: T201
    {"lang": dlc(message.from_user.language_code), "question": question},
    config={"configurable": {"session_id": {'user_id': user_id, 'lang_group': lang_group}}}
)

async def history_chat_stream(message: Message, chain: str, my_question: str | None = None) -> Iterator[BaseMessageChunk]:
    """Asynchronous chat with history and streaming"""

    message_text = my_question or message.text
    user_id = message.from_user.id
    lang_group = 'eng' if chain == 'english' else 'oth'

    if len(users.get_user_history(user_id, lang_group).messages) > 4:
        del users.get_user_history(user_id, lang_group).messages[:2]
        print(len(users.get_user_history(user_id, lang_group).messages))

    if message.quote:
        question = f"«{message.quote.text}»\n{message_text}"
    elif message.reply_to_message:
        question = f"«{message.reply_to_message.text}»\n{message_text}"
    else:
        question = message_text

    return available_models[chain].stream(
    {"lang": dlc(message.from_user.language_code), "question": question},
    config={"configurable": {"session_id": {'user_id': user_id, 'lang_group': lang_group}}}
)
