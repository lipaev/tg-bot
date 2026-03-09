import logging
from os import getenv
from aiogram import Bot
from google import genai
from src.users import Users
from dotenv import load_dotenv
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
#from random import shuffle

load_dotenv('.env')

bot = Bot(token=getenv('VEAPIL_BOT'))
genai_client = genai.Client()


model_names = {
    'flash': 'Gemini 2.5 Flash📝',
    'flash_2.0': 'Gemini 2.0 Flash📝',
    'flash_2.5_lite': 'Gemini 2.5 Flash Lite📝',
    'english': 'Учитель английского📝',
    'pro': 'Gemini 2.5 Pro📝',
    'tools': 'Gemini with tools',
    'flux': 'FLUX.1 [dev]📸',
    'rag': 'Закон РБ',
    'umbriel_gemini': 'Umbriel Gemini',
    'andrew_bing': 'Andrew Bing',
    'brian_bing': 'Brian Bing',
    'ava_bing': 'Ava Bing',
    "algenib": "Algenib Gemini",
    "charon": "Charon Gemini",
    "gemini-flash-image": "Gemini 2.0 Flash Image📸"
}

cipher = list(getenv('CIPHER'))
#shuffle(cipher)

# Set up file handler for DEBUG and above
file_handler = RotatingFileHandler('logs/logs.log', 'a', 1024 * 500, 1, 'utf-8', True)
#file_handler = logging.FileHandler('logs.log', 'w', 'utf-8', True)
file_handler.setLevel(logging.DEBUG)

# Set up stream handler for INFO and above
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Common formatter
formatter = logging.Formatter(
    '({asctime}) [{levelname}] [{filename}:{lineno}] [{name}] --> {message}',
    style='{'
)
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, stream_handler])

@dataclass
class Config:
    bot: Bot
    bot_token: str
    admin_ids: list[int]
    google_api_key: str
    hf_api_key: str
    #ds_api_key: str
    model_names: dict[str, str]
    users: Users
    cipher: str
    logging: logging
    sqlconninfo: str
    genai_client: genai.Client

config = Config(
    bot=bot,
    bot_token=getenv('VEAPIL_BOT'),
    admin_ids=[int(getenv('ADMIN_ID'))],
    google_api_key=getenv('GOOGLE_API_KEY'),
    hf_api_key=getenv('HF_API_KEY'),
    #ds_api_key=getenv('DEEPSEEK_API_KEY'),
    model_names=model_names,
    users=Users(),
    cipher=''.join(cipher),
    logging=logging,
    sqlconninfo=getenv("SQLCONNINFO"),
    genai_client=genai_client
    )