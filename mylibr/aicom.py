from typing import List, Iterator
from pydantic import BaseModel, Field
#import requests
#import aiohttp
#import chromadb
#from rag_solutions.chromadb_handler import get_or_create_chroma_collection, format_docs_chroma, collection_request
from rag_solutions.faiss_handler import load_faiss_db, create_faiss_retriever, format_docs_faiss

from aiogram.types import Message

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, BaseMessageChunk
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_community.tools import AskNewsSearch
#from langchain.schema import StrOutputParser

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

def get_by_session_id(session_id: dict) -> BaseChatMessageHistory:
    user_id = session_id['user_id']
    chat = session_id['chat']
    if user_id not in store[chat]:
        store[chat][user_id] = InMemoryHistory()
    return store[chat][user_id]

store = {'eng': {}, 'oth': {}}

db = load_faiss_db(db_path="faiss_db_tkrb", model="cointegrated/LaBSE-en-ru", index_name="codes_LaBSE")
retriever = create_faiss_retriever(db)

#chroma_client = chromadb.PersistentClient()
#chroma_collection = get_or_create_chroma_collection(chroma_client, name="codes", model_name="cointegrated/LaBSE-en-ru")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Your name is TipTop. You are a smart and helpful bot. Your interlocutor knows {lang} language well."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")])

template_rag = """
Ниже приведены фрагменты документа. Используй их для ответа на вопрос.

Context:
{context}

Question:
{question}

Answer:
"""

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
        prompt | ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=1, max_output_tokens=4096),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")

chain_pro_history = RunnableWithMessageHistory(
        prompt | ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=1, max_output_tokens=4096),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")

chain_english_history = RunnableWithMessageHistory(
        prompt_english | ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.6, max_output_tokens=4096),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")

chain_rag = (
    {"context": RunnableLambda(lambda x: retriever.invoke(x["question"])) | format_docs_faiss, "question": RunnablePassthrough()}
    | ChatPromptTemplate.from_template(template_rag)
    | ChatGoogleGenerativeAI(model="models/gemini-2.0-flash-001", temperature=1, top_p=1)
    #models/gemini-2.0-flash-001
    #models/gemini-2.5-pro-exp-03-25
    #| StrOutputParser()
)

chain_news = RunnableLambda(lambda x: AskNewsSearch().invoke(x['question'])) \
    | PromptTemplate(template="На основании следующих новостей сделай свою детальную новостную статью на русском языке с упоминанием источников.\n{news}") \
        | ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=1)

chains = {'mini': chain_course_history,
          'flash': chain_flash_history,
          'pro': chain_pro_history,
          'english': chain_english_history,
          'news': chain_news,
          'rag': chain_rag}

async def history_chat(message: Message, chain: str, my_question: str | None = None) -> BaseMessage:
    """Asyncсhronous chat with history"""

    message_text = my_question or message.text
    chat = 'eng' if chain == 'english' else 'oth'

    if store[chat].get(message.from_user.id, False) and len(store[chat][(message.from_user.id)].messages) > 44:
        del store[chat][(message.from_user.id)].messages[:2]
        print(len(store[chat][(message.from_user.id)].messages))

    if message.quote:
        question = f"«{message.quote.text}»\n{message_text}"
    elif message.reply_to_message:
        question = f"«{message.reply_to_message.text}»\n{message_text}"
    else:
        question = message_text

    return chains[chain].invoke(  # noqa: T201
    {"lang": dlc(message.from_user.language_code), "question": question},
    config={"configurable": {"session_id": {'user_id': message.from_user.id, 'chat': chat}}}
)

async def history_chat_stream(message: Message, chain: str, my_question: str | None = None) -> Iterator[BaseMessageChunk]:
    """Asynchronous chat with history and streaming"""

    message_text = my_question or message.text
    chat = 'eng' if chain == 'english' else 'oth'

    if store[chat].get(message.from_user.id, False) and len(store[chat][(message.from_user.id)].messages) > 44:
        del store[chat][(message.from_user.id)].messages[:2]
        print(len(store[chat][(message.from_user.id)].messages))

    if message.quote:
        question = f"«{message.quote.text}»\n{message_text}"
    elif message.reply_to_message:
        question = f"«{message.reply_to_message.text}»\n{message_text}"
    else:
        question = message_text

    return chains[chain].stream(
    {"lang": dlc(message.from_user.language_code), "question": question},
    config={"configurable": {"session_id": {'user_id': message.from_user.id, 'chat': chat}}}
)
