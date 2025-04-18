from typing import Dict, Any
from mylibr.chains import UserChatHistory

class Store:
    def __init__(self):
        self.data: Dict[int, Dict[str, Any]] = {}
        self.eng: Dict[int, UserChatHistory] = {}
        self.oth: Dict[int, UserChatHistory] = {}

    def update_data(self, user_id: int, key: str, value: Any) -> None:
        if user_id not in self.data:
            self.data[user_id] = {}
        self.data[user_id][key] = value

    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        return self.data.get(user_id, {})

    def update_history(self, user_id: int, history_type: str, history: UserChatHistory) -> None:
        if history_type == "eng":
            self.eng[user_id] = history
        elif history_type == "oth":
            self.oth[user_id] = history
        else:
            raise ValueError(f"Unknown history type: {history_type}")

    def get_history(self, user_id: int, history_type: str) -> UserChatHistory:
        if history_type == "eng":
            return self.eng.get(user_id, UserChatHistory())
        elif history_type == "oth":
            return self.oth.get(user_id, UserChatHistory())
        else:
            raise ValueError(f"Unknown history type: {history_type}")