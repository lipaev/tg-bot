from utils import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
load_dotenv()


def ask_ai(question: str) -> str:
    template = """Ты - TipTop, являешься телеграм ботом, который может общаться с людьми и отправлять им картинки с помощью команд указанных в /help.
    Тебе пользователь отправил такое сообщение: "{question}". Ответь на это сообщение без приветствия, если он сам не поприветствовал тебя."""

    prompt = PromptTemplate(template=template, input_variables=["question"])

    openai_llm = ChatOpenAI(temperature=0.0, course_api_key=os.getenv('COURSE_API_KEY'))

    llm_chain = prompt | openai_llm

    return llm_chain.invoke(question).content
