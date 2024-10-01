from aiogram.filters import BaseFilter
from aiogram.types import Message
import os
from logging import Filter, LogRecord

from dotenv import load_dotenv
load_dotenv()

class IsAdmin(BaseFilter):
    """
    Filter for admins
    """

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in eval(os.environ.get('ADMIN_IDS'))
    #   return {'is_admin': message.from_user.id in admin_ids}  в хендлер передаётся именованный аргумент

class WritingOnFile(Filter):
    """Filter for writing on file"""
    # Переменная рекорд ссылается на объект класса LogRecord
    def filter(self, record: LogRecord) -> bool:
        return record.levelname in ['WARNING', 'ERROR', 'CRITICAL']
