from dataclasses import dataclass
from os import getenv
from dotenv import load_dotenv
from src.users import Users
#from random import shuffle

load_dotenv('.env')

models = {'flash': 'Gemini 2.5 Flash',
          'english': 'Учитель английского',
          'pro': 'Gemini 2.5 Pro',
          'flux': 'FLUX.1 [dev]',
          'rag': 'Закон РБ'}
cipher = list(getenv('CIPHER'))
#shuffle(cipher)

@dataclass
class DatabaseConfig:
    database: str         # Название базы данных
    db_host: str          # URL-адрес базы данных
    db_user: str          # Username пользователя базы данных
    db_password: str      # Пароль к базе данных


@dataclass
class TgBot:
    token: str            # Токен для доступа к телеграм-боту
    admin_ids: list[int]  # Список id администраторов бота


@dataclass
class Config:
    tg_bot: TgBot
    google_api_key: str
    hf_api_key: str
    ds_api_key: str
    models: dict[str, str]
    users: Users
    cipher: str

config = Config(
    tg_bot=TgBot(
        token=getenv('VEAPIL_BOT'),
        admin_ids=[int(getenv('ADMIN_ID'))]
    ),
    google_api_key=getenv('GOOGLE_API_KEY'),
    hf_api_key=getenv('HF_API_KEY'),
    ds_api_key=getenv('DEEPSEEK_API_KEY'),
    models=models,
    users=Users(),
    cipher=''.join(cipher)
    )