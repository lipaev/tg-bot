from langchain.vectorstores import FAISS
#from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_core.embeddings.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

class SentenceTransformerEmbeddings(Embeddings):
    """Адаптер для использования SentenceTransformer с LangChain."""

    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Генерация эмбеддингов для списка документов."""
        return self.model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        """Генерация эмбеддинга для одного запроса."""
        return self.model.encode(text, convert_to_numpy=True).tolist()

def load_faiss_db(db_path: str, model: str, index_name: str, allow_dangerous: bool = True):
    """Load FAISS database."""

    #embeddings = GoogleGenerativeAIEmbeddings(model=model)
    embedding_function = SentenceTransformerEmbeddings(model)
    return FAISS.load_local(db_path, embedding_function, index_name=index_name, allow_dangerous_deserialization=allow_dangerous)

def create_faiss_retriever(db: FAISS, search_type: str = "similarity_score_threshold", score_threshold: float = 0.2, k: int = 30):
    """Create a retriever from FAISS database."""

    return db.as_retriever(
        search_type=search_type,
        search_kwargs={"score_threshold": score_threshold, 'k': k}
    )

def format_docs_faiss(docs):
    return "\n\n".join([d.page_content for d in docs])

# The source of the data is trusted, hence setting allow_dangerous_deserialization to True is safe in this context.
# FAISS setup
#db = load_faiss_db(
#    db_path="faiss_db_tkrb",
#    model="models/text-embedding-004",
#    index_name="codes_LaBSE"
#)
#retriever = create_faiss_retriever(db)
##"context": RunnableLambda(lambda x: retriever.invoke(x["question"])) | format_docs_faiss,