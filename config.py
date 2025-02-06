from dataclasses import dataclass
from os import getenv
from dotenv import load_dotenv
load_dotenv('.env')

models = {'flash': 'Gemini 1.5 Flash',
          'english': 'Учитель английского',
          'mini': 'GPT 4o Mini',
          'pro': 'Gemini 1.5 Pro',
          'flux': 'FLUX.1 [dev]',
          'news': 'AskNewsAI'}

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
    course_api_key: str
    hf_api_key: str
    ds_api_key: str
    models: dict[str, str]

config = Config(
    tg_bot=TgBot(
        token=getenv('VEAPIL_BOT'),
        admin_ids=eval(getenv('ADMIN_IDS'))
    ),
    google_api_key=getenv('GOOGLE_API_KEY'),
    course_api_key=getenv('COURSE_API_KEY'),
    hf_api_key=getenv('HF_API_KEY'),
    ds_api_key=getenv('DEEPSEEK_API_KEY'),
    models=models
    )