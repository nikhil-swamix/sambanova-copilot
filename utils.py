

# This will automatically use the environment variable VOYAGE_API_KEY.
# Alternatively, you can use vo = voyageai.Client(api_key="<your secret key>")


import voyageai
from chromadb import Documents, EmbeddingFunction, Embeddings

class VoyageEmbedFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        # embed the documents somehow
        vo = voyageai.Client()
        result = vo.embed(documents, model="voyage-3").embeddings
        print(result)
        return embeddings
