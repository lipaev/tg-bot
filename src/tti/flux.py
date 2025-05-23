import aiohttp
from aiogram.types import Message, BufferedInputFile
from config import config
from huggingface_hub import InferenceClient

async def generate_flux_photo_old(message: Message, my_question: str | None = None) -> BufferedInputFile:

    if my_question:
        message_text = my_question
    else:
        message_text = message.text

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev",
                                headers={"Authorization": f"Bearer {config.hf_api_key}"},
                                json={"inputs": message_text}) as response:
            response = await response.content.read()

    return BufferedInputFile(response, filename='photo.jpg')

async def generate_flux_photo(message: Message, my_question: str | None = None) -> BufferedInputFile:

    if my_question:
        message_text = my_question
    else:
        message_text = message.text

    client = InferenceClient(
    provider="fal-ai",
    api_key=config.hf_api_key,
    )

    # output is a PIL.Image object
    image = client.text_to_image(
        message_text,
        model="black-forest-labs/FLUX.1-dev",
    )

    return BufferedInputFile(image, filename='photo.jpg')
