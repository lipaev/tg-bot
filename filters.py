from aiogram.filters import BaseFilter
from aiogram.types import Message
import os
from dotenv import load_dotenv
load_dotenv()

class IsAdmin(BaseFilter):
    """
    Filter for admins
    """

    async def __call__(self, message: Message) -> str:
        return message.from_user.id in eval(os.environ.get('ADMIN_IDS'))

    # if message.from_user.id in admin_ids:
    #    return {'is_admin': True}  в хендлер передаётся именованный аргумент
