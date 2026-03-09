from langchain_core.messages import BaseMessage, BaseMessageChunk
from langchain_core.runnables.history import RunnableWithMessageHistory
from typing import Iterator, Any
from aiogram.types import Message
from config import config
from dataclasses import dataclass, field

from src.ttt.utils import google_chain, prompt_english
# from src.ttt.faiss_rag import chain_rag
# from src.tti.flux import generate_flux_photo
from src.tti.gemini import send_tti_message
from src.tts import bing, gemini
from src.stt import faster_whisper # whisper

from .tools import decode_language_code


available_models = {
    "ttt": {
        "flash": {"model": google_chain(), "description": "Gemini 2.5 Flash"},
        "flash_2.5_lite": {"model": google_chain("models/gemini-flash-lite-latest"), "description": "Gemini 2.5 Flash Lite"},
        "english": {"model": google_chain(prompt=prompt_english, temperature=0.8), "description": "Учитель английского"},
        # "rag": chain_rag,
        'pro': {"model": google_chain("models/gemini-2.5-pro", temperature=0.7), "description": "Gemini 2.5 Pro"},
    },
    "tti": {
        #'flux': generate_flux_photo,
        "gemini-flash-image": {"model": send_tti_message, "description": "Gemini 2.0 Flash Image📸"}
    },
    "tts": {
        "algenib": {"model": gemini.send_tts_message("Algenib"), "description": "Algenib"},
        "charon": {"model": gemini.send_tts_message("Charon"), "description": "Charon"},
        "andrew_bing": {"model": bing.send_tts_message("en-US-AndrewMultilingualNeural"), "description": "Andrew Bing"},
        "brian_bing": {"model": bing.send_tts_message("en-US-BrianMultilingualNeural"), "description": "Brian Bing"},
        "ava_bing": {"model": bing.send_tts_message("en-US-AvaMultilingualNeural"), "description": "Ava Bing"},
    },
    "stt": {
        #"whisper": whisper.speech_to_text,
        "faster-whisper": {"model": faster_whisper.speech_to_text, "description": "Faster Whisper"},
    },
}


# @dataclass
# class BotModels():
#     models: dict[str, dict[str, Any]] = field(default_factory=(available_models["stt"] | available_models["tti"] | available_models["tts"] | available_models["ttt"]))
#     stt: dict[str, Any] = available_models["stt"]
#     tti: dict[str, Any] = available_models["tti"]
#     tts: dict[str, Any] = available_models["tts"]
#     ttt: dict[str, Any] = available_models["ttt"]

async def history_chat(
    message: Message,
    chain: str,
    message_text: str | None = None,
    stream: bool = True
) -> Iterator[BaseMessageChunk] | BaseMessage:
    """Asynchronous chat with history"""

    message_text = message_text or message.text
    user_id = message.from_user.id

    # If more than 80 messages from a user and a bot, then delete 2 oldest messages.
    if len(config.users.get_user_history(user_id).messages) > 80:
        del config.users.get_user_history(user_id).messages[:2]
        config.logging.info(
            f'2 oldest messages have been deleted.'
        )

    if message.quote:
        message_text = f"«{message.quote.text}»\n{message_text}"
    elif message.reply_to_message:
        message_text = f"«{message.reply_to_message.text}»\n{message_text}"

    settings = {
            "configurable": {
                "session_id": {"user_id": user_id}
            }
        }

    chain: RunnableWithMessageHistory = available_models["ttt"][chain]['model']
    if stream:
        return chain.stream(
            {
                "lang": decode_language_code(message.from_user.language_code),
                "question": message_text,
            },
            config=settings,
        )
    else:
        return chain.invoke(
            {
                "lang": decode_language_code(message.from_user.language_code),
                "question": message_text,
            },
            config=settings,
        )
