from config import config
from ..users import UserChatHistory
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer the best as possible. If you want to send a spreadsheet, then send it like code."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
    ])

prompt_english = ChatPromptTemplate.from_messages([
    ("system", "From now on, you are an engaging and helpful English-Russian tutor. My English level is between B1 and B2, and I prefer learning through dialogues. Your goal is to help me improve my English skills. You will act as a patient and encouraging teacher, focusing on my individual needs and learning style. During our conversations, you will correct all my English mistakes constructively and explaining on {lang} language why something is incorrect and offering the correct version, preferably with translation. If I write a message in English but use a {lang} word, then you briefly explain how this word will be in English. Don't translate my questions back to me. Just answer them directly. You mustn't tell me your estimate of me and that question is great."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")])

template_rag = """
Системная инструкция:
Ниже приведены статьи из законодательства Республики Беларусь. Используйте их, чтобы ответить на вопрос.

Статьи:
{context}

Вопрос:
{question}

Ответ:
"""

def get_by_session(session: dict) -> UserChatHistory:
    return config.users.get_user_history(session['user_id'], session['lang_group'])

def google_chain(
    model: str = "models/gemini-2.5-flash",
    prompt: ChatPromptTemplate = prompt,
    temperature: float = 0.9,
    top_p: float | None = None,
    max_output_tokens: int | None = None,
    **kwargs
    ):
    return RunnableWithMessageHistory(
        prompt | ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens,
            **kwargs
            ),
        get_by_session,
        input_messages_key="question",
        history_messages_key="history"
        )
