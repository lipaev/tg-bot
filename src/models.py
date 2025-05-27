from langchain_core.messages import BaseMessage, BaseMessageChunk
from typing import Iterator
from aiogram.types import Message
from config import config

#from src.tti.flux import generate_flux_photo
from src.tti.gemini import send_tti_message
from src.tts import bing, gemini
from src.stt.whisper import speach_to_text
from src.ttt.utils import chain, prompt_english
#from src.ttt.faiss_rag import chain_rag

from .tools import decode_language_code


available_models = {
    'ttt': {
        'flash': chain(),
        "flash_2.0": chain('models/gemini-2.0-flash'),
        'english': chain(prompt=prompt_english, temperature=0.6),
        #"rag": chain_rag,
        #'pro': chain("models/gemini-2.5-pro-exp-03-25", temperature=1),
    },
    'tti': {
        #'flux': generate_flux_photo,
        'gemini-flash-image': send_tti_message
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

async def history_chat(
    message: Message,
    chain: str,
    message_text: str | None = None,
    stream: bool = True
    ) -> Iterator[BaseMessageChunk] | BaseMessage:
    """Asynchronous chat with history"""

    message_text = message_text or message.text
    user_id = message.from_user.id
    lang_group = 'eng' if chain == 'english' else 'oth'

    if len(config.users.get_user_history(user_id, lang_group).messages) > 44:
        del config.users.get_user_history(user_id, lang_group).messages[:2]
        print(len(config.users.get_user_history(user_id, lang_group).messages))

    if message.quote:
        message_text = f"«{message.quote.text}»\n{message_text}"
    elif message.reply_to_message:
        message_text = f"«{message.reply_to_message.text}»\n{message_text}"

    if stream:
        return available_models['ttt'][chain].stream(
            {"lang": decode_language_code(message.from_user.language_code), "question": message_text},
            config={"configurable": {"session_id": {'user_id': user_id, 'lang_group': lang_group}}}
        )
    else:
        return available_models['ttt'][chain].invoke(
            {"lang": decode_language_code(message.from_user.language_code), "question": message_text},
            config={"configurable": {"session_id": {'user_id': user_id, 'lang_group': lang_group}}}
        )