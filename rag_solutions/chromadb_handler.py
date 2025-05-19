from chromadb.api import ClientAPI
from chromadb import Collection, QueryResult
from chromadb.api.types import EmbeddingFunction
from sentence_transformers import SentenceTransformer
from numpy import ndarray

class SentenceTransformerEmbeddingFunction(EmbeddingFunction[str]):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: str) -> ndarray:
        return self.model.encode(input, convert_to_numpy=True)

def get_or_create_chroma_collection(client: ClientAPI, name: str, model_name: str) -> Collection:
    """Get or create a ChromaDB collection."""
    embedding_function = SentenceTransformerEmbeddingFunction(model_name)
    return client.get_or_create_collection(name=name, embedding_function=embedding_function)

def add_documents_to_chroma(collection: Collection, documents, ids) -> None:
    """Add documents to ChromaDB collection."""
    collection.upsert(documents=documents, ids=ids)

def collection_request(collection: Collection, question: str, n_results: int=15) -> QueryResult:

    results = collection.query(
        query_texts=[question], # Chroma will embed this for you
        include=["documents"],
        n_results=n_results # how many results to return
    )
    return results["documents"][0]

def format_docs_chroma(results: list[str]) -> str:
    return "\n".join(results)