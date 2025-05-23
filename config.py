from dataclasses import dataclass
from aiogram import Bot
from os import getenv
from dotenv import load_dotenv
from src.users import Users
import logging
#from random import shuffle

load_dotenv('.env')

bot = Bot(token=getenv('VEAPIL_BOT'))


model_names = {
    'flash': 'Gemini 2.5 Flash',
    'english': 'Учитель английского',
    'pro': 'Gemini 2.5 Pro',
    'flux': 'FLUX.1 [dev]',
    'rag': 'Закон РБ',
    'umbriel_gemini': 'Umbriel Gemini',
    'andrew_bing': 'Andrew Bing',
    'ava_bing': 'Ava Bing',
    "algenib": "Algenib Gemini",
    "charon": "Charon Gemini",
}

cipher = list(getenv('CIPHER'))
#shuffle(cipher)

# Set up file handler for DEBUG and above
file_handler = logging.FileHandler('logs.log', 'w', 'utf-8', True)
file_handler.setLevel(logging.DEBUG)

# Set up stream handler for INFO and above
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Common formatter
formatter = logging.Formatter(
    '{asctime}|{levelname:7}|{filename}:{lineno}|{name}|{message}',
    style='{'
)
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, stream_handler])

# @dataclass
# class DatabaseConfig:
#     database: str         # Название базы данных
#     db_host: str          # URL-адрес базы данных
#     db_user: str          # Username пользователя базы данных
#     db_password: str      # Пароль к базе данных

@dataclass
class Config:
    bot: Bot
    admin_ids: list[int]
    google_api_key: str
    hf_api_key: str
    ds_api_key: str
    model_names: dict[str, str]
    users: Users
    cipher: str
    logging: logging

config = Config(
    bot=bot,
    admin_ids=[int(getenv('ADMIN_ID'))],
    google_api_key=getenv('GOOGLE_API_KEY'),
    hf_api_key=getenv('HF_API_KEY'),
    ds_api_key=getenv('DEEPSEEK_API_KEY'),
    model_names=model_names,
    users=Users(),
    cipher=''.join(cipher),
    logging=logging
    )