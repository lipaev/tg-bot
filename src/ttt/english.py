from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from .utils import get_by_session_id

prompt_english = ChatPromptTemplate.from_messages([
    ("system", "From now on, you are an engaging and helpful English tutor named TipTop. My English level is between A1 and A2, and I prefer learning through dialogues. Your goal is to help me improve my English skills. You will act as a patient and encouraging teacher, focusing on my individual needs and learning style. During our conversations, you will correct all my English mistakes constructively and explaining on {lang} language why something is incorrect and offering the correct version, preferably with translation in brackets. If I write a message in English but use a {lang} word, then you briefly explain how this word will be in English. Don't translate my questions back to me. Just answer them directly."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")])

chain_english_history = RunnableWithMessageHistory(
        prompt_english | ChatGoogleGenerativeAI(model="models/gemini-2.5-flash-preview-04-17", temperature=0.6, max_output_tokens=65536),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")