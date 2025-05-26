from langchain_community.vectorstores import FAISS
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
    """
    Loads a FAISS database from a local path using the specified embedding model and index name.

    Args:
        db_path (str): The file path to the FAISS database.
        model (str): The name of the embedding model to use for loading the database.
        index_name (str): The name of the index to load from the FAISS database.
        allow_dangerou (bool, optional): Whether to allow potentially unsafe deserialization. Defaults to True.

    Returns:
        FAISS: The loaded FAISS database object.
    """

    #embeddings = GoogleGenerativeAIEmbeddings(model=model)
    embedding_function = SentenceTransformerEmbeddings(model)
    return FAISS.load_local(db_path, embedding_function, index_name=index_name, allow_dangerous_deserialization=allow_dangerous)

def create_faiss_retriever(db: FAISS, search_type: str = "similarity_score_threshold", score_threshold: float = 0.2, k: int = 30):
    """
    Creates a FAISS retriever instance with the specified search parameters.
    Args:
        db (FAISS): The FAISS database instance to use for retrieval.
        search_type (str, optional): The type of search to perform. Defaults to `"similarity_score_threshold"`.
        score_threshold (float, optional): The minimum similarity score threshold for retrieved results. Defaults to 0.2.
        k (int, optional): The maximum number of results to retrieve. Defaults to 30.
    Returns:
        FAISSRetriever: A configured FAISS retriever instance.
    """

    return db.as_retriever(
        search_type=search_type,
        search_kwargs={"score_threshold": score_threshold, 'k': k}
    )

def format_docs_faiss(docs):
    return "\n\n".join([d.page_content for d in docs])
