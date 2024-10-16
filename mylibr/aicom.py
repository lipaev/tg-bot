from typing import List, Iterator
from pydantic import BaseModel, Field
import requests

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
        self.messages.extend([type(message)(message.content) for message in messages])

    def clear(self) -> None:
        self.messages = []

def get_by_session_id(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryHistory()
    return store[session_id]

store = {}

prompt = ChatPromptTemplate.from_messages([
    ("system", "Your name is TipTop. You are a smart and helpful bot. Your interlocutor knows {lang} language well."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")])

prompt_english = ChatPromptTemplate.from_messages([
    ("system", "From now on, you are an engaging and helpful English tutor named TipTop. My English level is between A1 and A2, and I prefer learning through dialogues. Your goal is to help me improve my English skills. You will act as a patient and encouraging teacher, focusing on my individual needs and learning style. During our conversations, you will correct all my English mistakes constructively and explaining on {lang} language why something is incorrect and offering the correct version, preferably with translation in brackets. If I write a message in English but use a {lang} word, then you briefly explain how this word will be in English. Don't translate my questions back to me. Just answer them directly."),
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

chain_english_history = RunnableWithMessageHistory(
        prompt_english | ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.6, max_output_tokens=4096),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")

chains = {'mini': chain_course_history, 'flash': chain_flash_history, 'pro': chain_pro_history, 'english': chain_english_history}

async def history_chat(message: Message, chain: str) -> BaseMessage:
    """Asyncсhronous chat with history"""

    if store.get(message.from_user.id, False) and len(store[(message.from_user.id)].messages) > 44:
        del store[(message.from_user.id)].messages[:2]
        print(len(store[(message.from_user.id)].messages))

    if message.quote:
        question = f"«{message.quote.text}»\n{message.text}"
    elif message.reply_to_message:
        question = f"«{message.reply_to_message.text}»\n{message.text}"
    else:
        question = message.text

    return chains[chain].invoke(  # noqa: T201
    {"lang": dlc(message.from_user.language_code), "question": question},
    config={"configurable": {"session_id": message.from_user.id}}
)

async def history_chat_stream(message: Message, chain: str) -> Iterator[BaseMessageChunk]:
    """Asynchronous chat with history and streaming"""

    if store.get(message.from_user.id, False) and len(store[(message.from_user.id)].messages) > 44:
        del store[(message.from_user.id)].messages[:2]
        print(len(store[(message.from_user.id)].messages))

    if message.quote:
        question = f"«{message.quote.text}»\n{message.text}"
    elif message.reply_to_message:
        question = f"«{message.reply_to_message.text}»\n{message.text}"
    else:
        question = message.text

    return chains[chain].stream(
    {"lang": dlc(message.from_user.language_code), "question": question},
    config={"configurable": {"session_id": message.from_user.id}}
)

async def bytes_photo_flux(message: Message) -> None:

    response = requests.post(
     "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev",
     headers={"Authorization": f"Bearer {config.hf_api_key}"},
     json={"inputs": message.text})

    requests.post(f'https://api.telegram.org/bot{config.tg_bot.token}/sendPhoto?chat_id={message.chat.id}',
                        files={'photo': response.content})
    # You can access the image with PIL.Image for example
    #image = Image.open(io.BytesIO(image_bytes))
    #return response.content