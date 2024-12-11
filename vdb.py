from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Union
import os
import requests
from contextlib import suppress
import hashlib
import uuid


class VectorDB:
    def __init__(self, path=".workspace/vdb"):
        self.client = QdrantClient(path=path)
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY")
        self.default_collection = "mydocs"
        # with suppress(Exception):
        self.client.delete_collection(self.default_collection)

        with suppress(Exception):
            self.create_collection(self.default_collection)
        # index_md_files(self, read_md_files())

    def embed(self, texts: Union[str, List[str]], model: str = "voyage-3") -> List[List[float]]:
        if isinstance(texts, str):
            texts = [texts]
        response = requests.post(
            "https://api.voyageai.com/v1/embeddings", headers={"Authorization": f"Bearer {self.voyage_api_key}"}, json={"input": texts, "model": model}
        )
        return [item["embedding"] for item in response.json()["data"]]

    def create_collection(self, name: str, vector_size: int = 1024):
        return self.client.create_collection(collection_name=name, vectors_config=VectorParams(size=vector_size, distance=Distance.DOT))

    def insert_text(self, pid, text: str, metadata=None):
        point = {"id": pid, "vector": self.embed(text)[0], "payload": {"text": text, **(metadata or {})}}
        return self.client.upsert(collection_name=self.default_collection, points=[PointStruct(**point)], wait=False)

    def query(self, text: str = '', limit: int = 2):
        if text.strip() == "":
            return "Error Fetching from workspace documents"
        hits = self.client.search(collection_name=self.default_collection, query_vector=self.embed(text)[0], limit=limit)  # Return 5 closest points
        sep = "\n----------DOC----------\n"
        return sep + sep.join([f"File:{h.payload['filename']}\n{h.payload['text']}" for h in hits if h.payload])

    def delete_collection(self, name: str):
        return self.client.delete_collection(collection_name=name)

    def all_points(self, collection_name: str = None):
        collection_name = collection_name or self.default_collection
        return self.client.scroll(collection_name=collection_name, scroll_filter=None, limit=100000)


def read_md_files(directory=".workspace"):
    """Reads Markdown files from a directory and returns a list of tuples containing the file name and text."""
    md_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "r") as file:
                text = file.read()
                md_files.append((filename, text))
    return md_files


def index_md_files(vdb: VectorDB, md_files):
    """Indexes the Markdown files using the VectorDB."""
    for filename, text in md_files:
        pid = uuid.uuid5(uuid.NAMESPACE_DNS, filename)
        metadata = {"filename": filename}
        vdb.insert_text(str(pid), text, metadata)


def main():
    vdb = VectorDB()
    print()
    # print(vdb.all_points())

    print(vdb.query("ai chip troubleshooting"))

    # print("Indexed", len(md_files), "Markdown files.")


if __name__ == "__main__":
    main()
