from aiogram.filters import BaseFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message
from logging import Filter, LogRecord
from config import config


class IsAdmin(BaseFilter):
    """
    Filter for admins
    """

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.tg_bot.admin_ids
       #return {'is_admin': message.from_user.id in admin_ids}  в хендлер передаётся именованный аргумент

class WritingOnFile(Filter):
    """Filter for writing on file"""
    def filter(self, record: LogRecord) -> bool:
        return record.levelname in ['WARNING', 'ERROR', 'CRITICAL']

class ModelCallback(CallbackData, prefix='model'):
    model: str
    user_id: int