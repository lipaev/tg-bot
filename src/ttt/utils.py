from config import config
from ..users import UserChatHistory

def get_by_session_id(session_id: dict) -> UserChatHistory:
    return config.users.get_user_history(session_id['user_id'], session_id['lang_group'])