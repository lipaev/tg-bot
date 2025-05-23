from aiogram import Bot
from aiogram.types import Message
import aiohttp
import requests
from config import config


async def speach_to_text(message: Message, bot: Bot) -> str | None:

    file_info = await bot.get_file(message.voice.file_id)
    file_url = f'https://api.telegram.org/file/bot{config.bot_token}/{file_info.file_path}'

    API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
    headers = {"Authorization": f"Bearer {config.hf_api_key}"}

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, data=requests.get(file_url).content) as response:
            text_from_voice: dict[str, str] = await response.json()

    return text_from_voice.get('text', None)

async def speach_to_text_new(message: Message) -> str | None:

    file_info = await config.bot.get_file(message.voice.file_id)
    file_url = f'https://api.telegram.org/file/bot{config.bot_token}/{file_info.file_path}'

    API_URL = "https://router.huggingface.co/fal-ai/fal-ai/whisper"
    headers = {"Authorization": f"Bearer {config.hf_api_key}"}

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers={**headers, "Content-Type": "audio/flac"}, data=requests.get(file_url).content) as response:
            text_from_voice: dict[str, str] = await response.json()

    return text_from_voice.get('text', None)