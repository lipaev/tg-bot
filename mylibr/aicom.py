import os
from typing import List, AsyncIterator
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from aiogram.types import Message

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, BaseMessageChunk
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils import ChatOpenAI

load_dotenv('../.env')
api_key = os.getenv('COURSE_API_KEY')
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])


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
    ("system", "Тебя зовут - TipTop. Ты остроумный и умный бот. На сообщение пользователя тебе следует отвечать на '{lang}' языке"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")])

chain_course_history = RunnableWithMessageHistory(
        prompt | ChatOpenAI(temperature=1, course_api_key=api_key),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")

chain_flash_history = RunnableWithMessageHistory(
        prompt | ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1, max_output_tokens=4000),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")

chain_pro_history = RunnableWithMessageHistory(
        prompt | ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.1, max_output_tokens=4000),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")

chains = {'mini': chain_course_history, 'flash': chain_flash_history, 'pro': chain_pro_history}

async def history_chat(message: Message, chain: str = 'flash') -> BaseMessage:
    """Asyncсhronous chat with history"""

    if store.get(message.from_user.id, False) and len(store[(message.from_user.id)].messages) > 44:
        del store[(message.from_user.id)].messages[:2]
        print(len(store[(message.from_user.id)].messages))

    return await chains[chain].ainvoke(  # noqa: T201
    {"lang": message.from_user.language_code, "question": f"{message.text}"},
    config={"configurable": {"session_id": message.from_user.id}}
)

async def history_chat_stream(message: Message, chain: str = 'flash') -> AsyncIterator[BaseMessageChunk]:
    """Asynchronous chat with history and streaming"""

    if store.get(message.from_user.id, False) and len(store[(message.from_user.id)].messages) > 44:
        del store[(message.from_user.id)].messages[:2]
        print(len(store[(message.from_user.id)].messages))

    return chains[chain].stream(
    {"lang": message.from_user.language_code, "question": f"{message.text}"},
    config={"configurable": {"session_id": message.from_user.id}}
)
