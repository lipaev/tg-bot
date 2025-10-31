import io
import requests
from config import config
from faster_whisper import WhisperModel

model = WhisperModel(model_size_or_path="large-v3", device="cuda", compute_type="int8_float32")

async def speach_to_text(voice_file_id: str) -> str | None:

    file_info = await config.bot.get_file(voice_file_id)
    file_url = (
        f"https://api.telegram.org/file/bot{config.bot_token}/{file_info.file_path}"
    )

    segments, info = model.transcribe(
        io.BytesIO(requests.get(file_url).content),
        beam_size=5,
        # multilingual=False,
        language="en",
        without_timestamps=True,
    )

    transcript = ""

    for segment in segments:
        transcript += segment.text

    return transcript
