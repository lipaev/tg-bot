from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from .utils import get_by_session_id


prompt = ChatPromptTemplate.from_messages([
    ("system", "Your name is TipTop. You are a smart and helpful bot."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")])


chain_flash_history = RunnableWithMessageHistory(
        prompt | ChatGoogleGenerativeAI(model="models/gemini-2.5-flash-preview-04-17", temperature=1, max_output_tokens=65536),
        get_by_session_id, # Uses the get_by_session_id function defined in the example above.
        input_messages_key="question",
        history_messages_key="history")