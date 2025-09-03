from dataclasses import dataclass, field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, FunctionMessage, AIMessageChunk
from langchain_core.chat_history import BaseChatMessageHistory
from typing import List, Union
from pydantic import BaseModel, Field
import psycopg
from psycopg.sql import SQL, Identifier
from typing import Any
from os import getenv
from dotenv import load_dotenv
load_dotenv('.env')

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
    stream: bool = False
    temp: bool = False
    model: str = "flash"
    lang: str = "en"
    last_sh_his_id: int = 0
    english: UserChatHistory = field(default_factory=UserChatHistory)
    other: UserChatHistory = field(default_factory=UserChatHistory)
    temphis: UserChatHistory = field(default_factory=UserChatHistory)

class Users():
    """
    Class containing users information.
    """

    def __init__(self):
        self.dict: dict[int, User] = {}

    def last_sh_his_id(self, user_id: int):
        return self.dict.setdefault(user_id, User()).last_sh_his_id

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

    def get_user_history(self, user_id: int) -> UserChatHistory:
        if self.temp(user_id):
            return self.temphis(user_id)
        elif self.model(user_id) == "english":
            return self.english(user_id)
        else:
            return self.other(user_id)

    def load_from_db(self):
        """
        Loads users from the SQL table.
        """

        with psycopg.connect(getenv("SQLCONNINFO")) as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT id, stream, temp, model, lang, eng_his, oth_his FROM users')
                rows = cursor.fetchall()

                for row in rows:
                    user_id, stream, temp, model, lang, eng_his, oth_his = row

                    english_history = UserChatHistory.model_validate(eng_his) if eng_his else UserChatHistory()
                    other_history = UserChatHistory.model_validate(oth_his) if oth_his else UserChatHistory()

                    self.add_user(
                        user_id,
                        stream=stream,
                        temp=temp,
                        model=model,
                        lang=lang,
                        english=english_history,
                        other=other_history
                    )

async def update_user_data(id: int, parameter: str, value, sqlconninfo: str) -> None:
    """
    Updates a specific parameter for a user in the database.
    Args:
        id (int): The ID of the user whose parameter is to be updated.
        parameter (str): The name of the parameter/column to update.
        value: The new value to set for the specified parameter.
    Returns:
        None
    Raises:
        sqlite3.Error: If a database error occurs during the operation.
    """

    allowed_columns = {"stream", "temp", "model", "block", "eng_his", "oth_his"}
    if parameter not in allowed_columns:
        raise ValueError(f"Invalid column name: {parameter}")

    with psycopg.connect(sqlconninfo, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(SQL('UPDATE users SET {} = %s WHERE id = %s').format(Identifier(parameter)), (value, id))

async def get_user_data(user_id: int, columns: list[str] | str, sqlconninfo: str) -> tuple | Any | None:
    if isinstance(columns, str):
        columns = [columns]
    with psycopg.connect(sqlconninfo) as conn:
        with conn.cursor() as cur:
            cur.execute(
                SQL('SELECT {columns} FROM users WHERE id = %s').format(
                    columns=SQL(',').join([Identifier(column) for column in columns])
                    ),
                (user_id,)
            )
            result = cur.fetchone()
            if len(result) == 1:
                return result[0]
            return result