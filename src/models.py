from langchain_core.messages import BaseMessage, BaseMessageChunk
from typing import Iterator
from aiogram.types import Message
from config import config

# from src.tti.flux import generate_flux_photo
from src.tti.gemini import send_tti_message
from src.tts import bing, gemini
from src.stt import faster_whisper # whisper
from src.ttt.utils import google_chain, prompt_english
# from src.ttt.faiss_rag import chain_rag

from .tools import decode_language_code


available_models = {
    "ttt": {
        "flash": google_chain(),
        "flash_2.0": google_chain("models/gemini-2.0-flash"),
        "flash_2.5_lite": google_chain("models/gemini-2.5-flash-lite"),
        "english": google_chain(model="models/gemini-2.5-flash", prompt=prompt_english, temperature=0.6),
        # "rag": chain_rag,
        'pro': google_chain("models/gemini-2.5-pro", temperature=0.7),
    },
    "tti": {
        #'flux': generate_flux_photo,
        "gemini-flash-image": send_tti_message
    },
    "tts": {
        "algenib": gemini.send_tts_message("Algenib"),
        "charon": gemini.send_tts_message("Charon"),
        "andrew_bing": bing.send_tts_message("en-US-AndrewMultilingualNeural"),
        "ava_bing": bing.send_tts_message("en-US-AvaMultilingualNeural"),
    },
    "stt": {
        #"whisper": whisper.speach_to_text,
        "faster-whisper": faster_whisper.speach_to_text,
    },
}


async def history_chat(
    message: Message, chain: str, message_text: str | None = None, stream: bool = True
) -> Iterator[BaseMessageChunk] | BaseMessage:
    """Asynchronous chat with history"""

    message_text = message_text or message.text
    user_id = message.from_user.id

    # Set up a chat where the history will be saved.
    if config.users.temp(user_id):
        lang_group = "temphis"
    elif chain == "english":
        lang_group = "eng"
    else:
        lang_group = "oth"

    # If more than 80 messages from a user and a bot, then delete 2 oldest messages.
    if len(config.users.get_user_history(user_id, lang_group).messages) > 80:
        del config.users.get_user_history(user_id, lang_group).messages[:2]
        config.logging.info(
            f'2 oldest messages from the "{lang_group}" group have been deleted.'
        )

    if message.quote:
        message_text = f"«{message.quote.text}»\n{message_text}"
    elif message.reply_to_message:
        message_text = f"«{message.reply_to_message.text}»\n{message_text}"

    if stream:
        return available_models["ttt"][chain].stream(
            {
                "lang": decode_language_code(message.from_user.language_code),
                "question": message_text,
            },
            config={
                "configurable": {
                    "session_id": {"user_id": user_id, "lang_group": lang_group}
                }
            },
        )
    else:
        return available_models["ttt"][chain].invoke(
            {
                "lang": decode_language_code(message.from_user.language_code),
                "question": message_text,
            },
            config={
                "configurable": {
                    "session_id": {"user_id": user_id, "lang_group": lang_group}
                }
            },
        )
