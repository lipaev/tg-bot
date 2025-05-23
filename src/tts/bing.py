import asyncio
import edge_tts
from ..tools import lp
from .utils import voice_name
from aiogram.types import Message, BufferedInputFile
from config import config
from dotenv import load_dotenv
load_dotenv()

TEXT = """Example: When I was a child, I would play outside every day. (Когда я был ребенком, я играл на улице каждый день.)
My grandmother would tell us stories before bed. Моя бабушка рассказывала нам истории перед сном."""
OUTPUT_FILE = "src/tts/voice.mp3"


async def generate(
    text: str,
    voice_name: str='en-US-AndrewMultilingualNeural',
    save: bool = True
    ) -> dict[bytes, str]:
    """Main function

    Args:
        text: The text that will be read aloud.
        model_name: `en-US-AndrewMultilingualNeural`, `en-US-AvaMultilingualNeural`
        save: If True, the audio will be saved to a file. Defaults to True.

    Returns:
        dict: A dictionary containing the audio data and the name of the output file.
    """

    OUTPUT_FILE = f"src/tts/test/{voice_name}.mp3"

    communicate = edge_tts.Communicate(
        text,
        voice_name,
        volume = "+10%"
        )
    audio = b""
    async for i in communicate.stream():
        if i['type'] == 'audio':
            audio += i['data']
    if save:
        with open(OUTPUT_FILE, "wb") as out:
            out.write(audio)
    return {'voice': audio, 'name': OUTPUT_FILE}

@voice_name
async def send_tts_message(message: Message, text: str, voice_name: str) -> None:

    bot = config.bot

    # await bot.send_chat_action(
    #     message.chat.id,
    #     action="upload_voice",
    # )

    task = asyncio.create_task(lp(message.chat.id, cycles=16, action='upload_voice'))

    try:
        voice = await generate(text.replace('\\', ''), voice_name=voice_name, save=False)
        await bot.send_voice(
            message.chat.id,
            BufferedInputFile(voice['voice'], filename=voice['name']),
            reply_to_message_id=message.message_id,
            disable_notification=True
        )
    finally:
        task.cancel()


if __name__ == "__main__":
    asyncio.run(generate())