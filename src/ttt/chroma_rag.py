from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

import chromadb
from rag_solutions.chromadb_handler import get_or_create_chroma_collection, format_docs_chroma, collection_request
from .utils import template_rag


chroma_client = chromadb.PersistentClient("./rag_solutions/chroma")
chroma_collection = get_or_create_chroma_collection(chroma_client, name="codes", model_name="cointegrated/LaBSE-en-ru")


chain_rag = (
    {"context": RunnableLambda(lambda x: collection_request(chroma_collection, x["question"], 30)) | format_docs_chroma, "question": RunnablePassthrough()}
    | ChatPromptTemplate.from_template(template_rag)
    | ChatGoogleGenerativeAI(model="models/gemini-2.5-pro-exp-03-25", temperature=0.9, top_p=0.8, max_output_tokens=65536)
)