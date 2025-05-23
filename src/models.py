from langchain_core.messages import BaseMessage, BaseMessageChunk
from typing import Iterator
from aiogram.types import Message
from config import config

#from .ttt.pro import chain_pro_history
from src.ttt.flash import chain_flash_history
from src.ttt.english import chain_english_history
#from src.tti.flux import generate_flux_photo
from src.tts import bing, gemini
from src.stt.whisper import speach_to_text

from .tools import decode_language_code

available_models = {
    'ttt': {
        'flash': chain_flash_history,
        #'pro': chain_pro_history,
        'english': chain_english_history,
    },
    'tti': {
        #'flux': generate_flux_photo,
    },
    'tts': {
        "algenib": gemini.send_tts_message("Algenib"),
        "charon": gemini.send_tts_message("Charon"),
        'andrew_bing': bing.send_tts_message('en-US-AndrewMultilingualNeural'),
        'ava_bing': bing.send_tts_message('en-US-AvaMultilingualNeural')
    },
    'stt': {
        'whisper': speach_to_text
    }
}

async def history_chat(message: Message, chain: str, my_question: str | None = None) -> BaseMessage:
    """Asyncсhronous chat with history"""

    message_text = my_question or message.text
    user_id = message.from_user.id
    lang_group = 'eng' if chain == 'english' else 'oth'

    if len(config.users.get_user_history(user_id, lang_group).messages) > 44:
        del config.users.get_user_history(user_id, lang_group).messages[:2]
        print(len(config.users.get_user_history(user_id, lang_group).messages))

    if message.quote:
        question = f"«{message.quote.text}»\n{message_text}"
    elif message.reply_to_message:
        question = f"«{message.reply_to_message.text}»\n{message_text}"
    else:
        question = message_text

    return available_models['ttt'][chain].invoke(  # noqa: T201
    {"lang": decode_language_code(message.from_user.language_code), "question": question},
    config={"configurable": {"session_id": {'user_id': user_id, 'lang_group': lang_group}}}
)

async def history_chat_stream(message: Message, chain: str, my_question: str | None = None) -> Iterator[BaseMessageChunk]:
    """Asynchronous chat with history and streaming"""

    message_text = my_question or message.text
    user_id = message.from_user.id
    lang_group = 'eng' if chain == 'english' else 'oth'

    if len(config.users.get_user_history(user_id, lang_group).messages) > 44:
        del config.users.get_user_history(user_id, lang_group).messages[:2]
        print(len(config.users.get_user_history(user_id, lang_group).messages))

    if message.quote:
        question = f"«{message.quote.text}»\n{message_text}"
    elif message.reply_to_message:
        question = f"«{message.reply_to_message.text}»\n{message_text}"
    else:
        question = message_text

    return available_models['ttt'][chain].stream(
    {"lang": decode_language_code(message.from_user.language_code), "question": question},
    config={"configurable": {"session_id": {'user_id': user_id, 'lang_group': lang_group}}}
)