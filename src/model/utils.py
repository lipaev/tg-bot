from typing import List,Union
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, FunctionMessage, AIMessageChunk
from langchain_core.chat_history import BaseChatMessageHistory


class UserChatHistory(BaseChatMessageHistory, BaseModel):
    """In memory implementation of chat message history."""

    # Explicitly define the possible concrete message types in a Union
    messages: List[Union[HumanMessage, AIMessageChunk, AIMessage, SystemMessage, FunctionMessage]] = Field(default_factory=list)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend([type(message)(message.content) for message in messages])

    def clear(self) -> None:
        self.messages = []


def get_by_session_id(session_id: dict) -> UserChatHistory:
    from config import config
    return config.users.get_user_history(session_id['user_id'], session_id['lang_group'])


template_rag = """
Системная инструкция:
Ниже приведены статьи из законодательства Республики Беларусь. Используйте их, чтобы ответить на вопрос.

Статьи:
{context}

Вопрос:
{question}

Ответ:
"""