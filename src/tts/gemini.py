import asyncio
import mimetypes
import struct
from config import config
from ..tools import lp
from aiogram.types import Message, BufferedInputFile
from .utils import voice_name
from google import genai
from google.genai import types
from google.genai.errors import ClientError
import os
from dotenv import load_dotenv
load_dotenv()

@voice_name
async def send_tts_message(message: Message, text: str, voice_name: str) -> None:

    task = asyncio.create_task(lp(message.chat.id, cycles=36, action='upload_voice'))

    bot = config.bot
    await bot.send_chat_action(message.chat.id, 'upload_voice')

    try:
        client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
        )

        model = "gemini-2.5-flash-preview-tts"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=text),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            temperature=0.8,
            response_modalities=[
                "audio",
            ],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
        )

        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            if chunk.candidates[0].content.parts[0].inline_data:
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)
                if file_extension is None:
                    file_extension = ".wav"
                    data_buffer = await convert_to_wav(inline_data.data, inline_data.mime_type)
                #if save:
                    #await save_binary_file(f"src/tts/test/{file_extension}", data_buffer)
            else:
                print(chunk.text)

        await bot.send_voice(
        message.chat.id,
        BufferedInputFile(data_buffer, filename='voice.wav'),
        reply_to_message_id=message.message_id,
        disable_notification=True)
    except ClientError as e:
        await bot.send_message(message.chat.id, e.message, disable_notification=True)
        config.logging.error(e.details)
    finally:
        task.cancel()

async def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = await parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

async def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be
        integers if found, otherwise None.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}

async def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")