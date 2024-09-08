from aiogram.filters import BaseFilter
from aiogram.types import Message
from key import admin_ids


class IsAdmin(BaseFilter):
    """
    Filter for admins
    """

    async def __call__(self, message: Message) -> str:
        return message.from_user.id in admin_ids

    # if message.from_user.id in admin_ids:
    #    return {'is_admin': True}  в хендлер передаётся именованный аргумент
