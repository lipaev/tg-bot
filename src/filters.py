from aiogram.filters import BaseFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message
from logging import Filter, LogRecord
from config import config
from .models import available_models


class IsAdmin(BaseFilter):
    """
    Filter for admins
    """

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.admin_ids
       #return {'is_admin': message.from_user.id in admin_ids}  в хендлер передаётся именованный аргумент

class WritingOnFile(Filter):
    """Filter for writing on file"""
    def filter(self, record: LogRecord) -> bool:
        return record.levelname in ['DEBUG', 'WARNING', 'ERROR', 'CRITICAL']

class ModelCallback(CallbackData, prefix='model', sep=config.cipher):
    model: str
    user_id: int

class TTSCallback(CallbackData, prefix='tts_model', sep=config.cipher):
        tts_model: str
        user_id: int
        #text: str

async def available_model(message: Message) -> str:
    """
    Checks if the user has access to the model. If he has no access, modifies the user's model. Returns the available model.

    Returns:
        available model
    """

    user_id = message.from_user.id
    user_model = config.users.model(user_id)

    if user_model in available_models['tts'] | available_models['stt'] | available_models['ttt'] | available_models['tti']:
        return user_model
    else:
        await config.bot.send_message(
            message.chat.id,
            f"Модель {config.model_names[user_model]} недоступна и заменена на {config.model_names['flash']}."
        )
        config.users.dict[user_id].model = 'flash'
        return 'flash'
