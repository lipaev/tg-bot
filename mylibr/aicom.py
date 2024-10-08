from typing import List, Iterator
from pydantic import BaseModel, Field

from aiogram.types import Message

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, BaseMessageChunk
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .features import decode_language_code as dlc
from config import config
from utils import ChatOpenAI

api_key = config.course_api_key
GOOGLE_API_KEY = config.google_api_key

class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    """In memory implementation of chat message history."""

    messages: List[BaseMessage] = Field(default_factory=list)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []

def get_by_session_id(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryHistory()
    return store[session_id]

store = {}

prompt = ChatPromptTemplate.from_messages([
    ("system", "Тебя зовут - TipTop. Ты умный и остроумный бот. Твой собеседник хорошо знает {lang} язык."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")])

chain_course_history = RunnableWithMessageHistory(
        prompt | ChatOpenAI(temperature=1, course_api_key=api_key),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")

chain_flash_history = RunnableWithMessageHistory(
        prompt | ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=1, max_output_tokens=4096),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")

chain_pro_history = RunnableWithMessageHistory(
        prompt | ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=1, max_output_tokens=4096),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")

chains = {'mini': chain_course_history, 'flash': chain_flash_history, 'pro': chain_pro_history}

async def history_chat(message: Message, chain: str) -> BaseMessage:
    """Asyncсhronous chat with history"""

    if store.get(message.from_user.id, False) and len(store[(message.from_user.id)].messages) > 44:
        del store[(message.from_user.id)].messages[:2]
        print(len(store[(message.from_user.id)].messages))

    return await chains[chain].ainvoke(  # noqa: T201
    {"lang": dlc(message.from_user.language_code), "question": f"{message.text}"},
    config={"configurable": {"session_id": message.from_user.id}}
)

async def history_chat_stream(message: Message, chain: str) -> Iterator[BaseMessageChunk]:
    """Asynchronous chat with history and streaming"""

    if store.get(message.from_user.id, False) and len(store[(message.from_user.id)].messages) > 44:
        del store[(message.from_user.id)].messages[:2]
        print(len(store[(message.from_user.id)].messages))

    return chains[chain].stream(
    {"lang": dlc(message.from_user.language_code), "question": f"{message.text}"},
    config={"configurable": {"session_id": message.from_user.id}}
)
