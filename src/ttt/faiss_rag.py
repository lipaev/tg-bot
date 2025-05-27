from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

from rag_solutions.faiss_handler import load_faiss_db, create_faiss_retriever, format_docs_faiss
from .utils import template_rag


db = load_faiss_db(
    db_path="rag_solutions/faiss_db_tkrb",
    model="sergeyzh/LaBSE-ru-sts",
    index_name="LaBSE-ru-sts"
    )
retriever = create_faiss_retriever(db)

chain_rag = (
    {"context": RunnableLambda(lambda x: retriever.invoke(x["question"])) | format_docs_faiss, "question": RunnablePassthrough()}
    | ChatPromptTemplate.from_template(template_rag)
    | ChatGoogleGenerativeAI(model="models/gemini-2.5-flash-preview-05-20", temperature=0.9, top_p=0.8, max_output_tokens=65536)
)