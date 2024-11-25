import chromadb
from chromadb.utils import embedding_functions
import uuid
import os
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps

from chromadb import Documents, EmbeddingFunction, Embeddings

# Configure logging with file handler
log_file = 'chromadb.log'
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

class VoyageEmbedFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        import voyageai

        # embed the documents somehow
        vo = voyageai.Client(os.getenv('VOYAGE_API_KEY'))
        result = vo.embed(documents, model="voyage-3").embeddings
        print(result)
        return embeddings


def exceptional(func):
    """Decorator to handle exceptions and logging"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the error with function name and arguments
            logger.error(
                f"Error in {func.__name__}: {str(e)}", 
                exc_info=True,
                extra={
                    'fn_args': args,
                    'fn_kwargs': kwargs
                }
            )
            raise
    return wrapper

class ChromaWrapper:
    def __init__(self, api_key: str, collection_name: str = "default_collection"):
        """Initialize ChromaDB wrapper with OpenAI embeddings"""
        self.client = chromadb.PersistentClient()
        self.embedding_function = VoyageEmbedFunction()
        self.collection = self.client.get_or_create_collection(
            name=collection_name, 
            embedding_function=self.embedding_function
        )
        logger.info(f"Initialized ChromaWrapper with collection: {collection_name}")

    @exceptional
    def add_documents(self, texts: list[str], metadatas: list[dict] = None, ids: list[str] = None):
        """Add multiple documents to the collection"""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
        logger.info(f"Added {len(texts)} documents to collection")
        return ids

    @exceptional
    def query(self, query_text: str, n_results: int = 5):
        """Query the collection and return most similar documents"""
        results = self.collection.query(query_texts=[query_text], n_results=n_results)
        logger.info(f"Queried collection with text: {query_text}")
        return results

    @exceptional
    def delete_documents(self, ids: list[str]):
        """Delete documents by their IDs"""
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from collection")

    @exceptional
    def update_documents(self, texts: list[str], ids: list[str], metadatas: list[dict] = None):
        """Update existing documents"""
        self.collection.update(documents=texts, metadatas=metadatas, ids=ids)
        logger.info(f"Updated {len(texts)} documents in collection")

    @exceptional
    def get_documents(self, ids: list[str] = None):
        """Retrieve documents by their IDs"""
        results = self.collection.get(ids=ids) if ids else self.collection.get()
        logger.info(f"Retrieved documents from collection")
        return results

    @exceptional
    def peek(self, limit: int = 10):
        """Preview documents in the collection"""
        results = self.collection.peek(limit)
        logger.info(f"Peeked {limit} documents from collection")
        return results

    @exceptional
    def count(self) -> int:
        """Get the number of documents in the collection"""
        count = self.collection.count()
        logger.info(f"Current document count: {count}")
        return count

    @exceptional
    def reset(self):
        """Reset/clear the entire collection"""
        self.collection.delete()
        logger.info("Collection reset successfully")

# Usage example:

# Initialize the wrapper
chroma = ChromaWrapper(api_key="your-openai-api-key", collection_name="my_collection")

# Add documents
texts = ["This is the first document", "This is the second document", "This is the third document"]
metadatas = [{"source": "doc1"}, {"source": "doc2"}, {"source": "doc3"}]

doc_ids = chroma.add_documents(texts, metadatas)

# Query documents
results = chroma.query("first document", n_results=2)
print(results)

# Get document count
count = chroma.count()
print(f"Total documents: {count}")

# Preview documents
preview = chroma.peek(5)
print(preview)

# Update documents
chroma.update_documents(texts=["Updated first document"], ids=[doc_ids[0]])

# Delete documents
chroma.delete_documents([doc_ids[0]])

# Reset collection
chroma.reset()
