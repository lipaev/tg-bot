import os
from operator import itemgetter
from typing import List, Optional
from dotenv import load_dotenv

from aiogram.types import Message

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from langchain.memory import ConversationBufferMemory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import Runnable
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from pydantic import BaseModel, Field
from langchain_core.runnables import (
    RunnableLambda,
    ConfigurableFieldSpec,
    RunnablePassthrough,
)

from utils import ChatOpenAI

load_dotenv()


class InMemoryHistory(BaseChatMessageHistory, BaseModel):
    """In memory implementation of chat message history."""

    messages: List[BaseMessage] = Field(default_factory=list)

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []


store = {}
api_key = os.getenv('COURSE_API_KEY')
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def get_by_session_id(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryHistory()
    return store[session_id]

prompt = ChatPromptTemplate.from_messages([
    ("system", "Твоё имя - TipTop. Ты высокоинтеллектуальный бот, который может общаться с людьми и делиться картинками животных."),
    # ("system", "You're an assistant who's good at {ability}"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

#settings gemini
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

course_llm = ChatOpenAI(temperature=0.2, course_api_key=api_key)
model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  safety_settings = {  # See https://ai.google.dev/gemini-api/docs/safety-settings
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
})
chat_session = model.start_chat()


#gemini_runnable = RunnableLambda(lambda question: model.generate_content(question).text, name="gemini")
#chat_session.send_message(question).text


chain = prompt | course_llm
chain_with_history = RunnableWithMessageHistory(
    chain,
    # Uses the get_by_session_id function defined in the example
    # above.
    get_by_session_id,
    input_messages_key="question",
    history_messages_key="history"
)

def chat_with_history(message: Message) -> str:

    return chain_with_history.invoke(  # noqa: T201
    {"question": f"{message.text}"},
    config={"configurable": {"session_id": f"{message.from_user.id}"}}
).content

def ask_ai(question: str) -> str:
    template = """Ты - TipTop, являешься телеграм ботом, который может общаться с людьми и отправлять им картинки с помощью команд указанных в /help.
    Тебе пользователь отправил такое сообщение: "{question}". Ответь на это сообщение без приветствия, если он сам не поприветствовал тебя."""

    prompt = PromptTemplate(template=template, input_variables=["question"])

    openai_llm = ChatOpenAI(temperature=0.0, course_api_key=api_key)

    llm_chain = prompt | openai_llm

    return llm_chain.invoke(question).content
