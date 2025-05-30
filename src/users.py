from dataclasses import dataclass, field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, FunctionMessage, AIMessageChunk
from langchain_core.chat_history import BaseChatMessageHistory
from typing import List, Union
from pydantic import BaseModel, Field
import sqlite3

class UserChatHistory(BaseChatMessageHistory, BaseModel):
    """In memory implementation of chat message history."""

    # Explicitly define the possible concrete message types in a Union
    messages: List[Union[HumanMessage, AIMessageChunk, AIMessage, SystemMessage, FunctionMessage]] = Field(default_factory=list)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend([type(message)(message.content) for message in messages])

    def clear(self) -> None:
        self.messages = []

@dataclass
class User():
    stream: int = False
    temp: int = 0
    model: str = "flash"
    lang: str = "en"
    english: UserChatHistory = field(default_factory=UserChatHistory)
    other: UserChatHistory = field(default_factory=UserChatHistory)
    temphis: UserChatHistory = field(default_factory=UserChatHistory)

class Users():
    """
    Class containing users information.
    """

    def __init__(self):
        self.dict: dict[int, User] = {}

    def stream(self, user_id: int):
        return self.dict.setdefault(user_id, User()).stream

    def temp(self, user_id: int):
        return self.dict.setdefault(user_id, User()).temp

    def model(self, user_id: int):
        return self.dict.setdefault(user_id, User()).model

    def lang(self, user_id: int):
        return self.dict.setdefault(user_id, User()).lang

    def english(self, user_id: int):
        return self.dict.setdefault(user_id, User()).english

    def other(self, user_id: int):
        return self.dict.setdefault(user_id, User()).other

    def temphis(self, user_id: int):
        return self.dict.setdefault(user_id, User()).temphis

    def add_user(self, user_id: int, **kwargs):
        self.dict[user_id] = User(**kwargs)

    def get_user_history(self, user_id: int, lang_group: str) -> UserChatHistory:
        if lang_group == 'eng':
            return self.english(user_id)
        elif lang_group == 'oth':
            return self.other(user_id)
        elif lang_group == 'temphis':
            return self.temphis(user_id)
        else:
            raise ValueError(f"Unsupported lang_group: {lang_group}")

    def load_from_db(self, db_path: str):
        """
        Loads users from the SQL table.

        Args:
            db_path: path to data base.
        """

        connection = sqlite3.connect(db_path)

        try:
            cursor = connection.cursor()
            cursor.execute('SELECT id, stream, temp, model, lang, eng_his, oth_his FROM users')
            rows = cursor.fetchall()

            for row in rows:
                user_id, stream, temp, model, lang, eng_his, oth_his = row

                english_history = UserChatHistory.model_validate_json(eng_his) if eng_his else UserChatHistory()
                other_history = UserChatHistory.model_validate_json(oth_his) if oth_his else UserChatHistory()

                self.add_user(
                    user_id,
                    stream=stream,
                    temp=temp,
                    model=model,
                    lang=lang,
                    english=english_history,
                    other=other_history
                )
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            connection.close()
