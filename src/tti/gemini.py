from google import genai
from google.genai import types
from dotenv import load_dotenv
import asyncio
from ..tools import lp
from aiogram.types import Message, BufferedInputFile
from config import config
from google.genai.errors import ClientError
load_dotenv()

async def send_tti_message(*, message: Message, voice_text: str) -> None:

    if voice_text:
        message_text = voice_text
    else:
        message_text = message.text

    bot = config.bot
    client = genai.Client()

    task = asyncio.create_task(lp(message.chat.id, cycles=16, action='upload_voice'))

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash-image-preview",
            contents=message_text,
            config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE']
            )
        )

        for part in response.candidates[0].content.parts:
            if part.text is not None:
                await bot.send_message(message.chat.id, part.text)
            elif part.inline_data is not None:
                await bot.send_photo(
                    message.chat.id,
                    BufferedInputFile(part.inline_data.data, filename='gemini-native-image.png')
                )
    except ClientError as e:
        await bot.send_message(message.chat.id, e.message, disable_notification=True)
        config.logging.error(e.details)
    finally:
        task.cancel()
