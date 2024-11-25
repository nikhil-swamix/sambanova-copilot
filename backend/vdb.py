from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue


class VectorDB:
    def __init__(self, path="./.workspace/vdb"):
        self.client = QdrantClient(path=path)

    def create_collection(self, name, vector_size=4, distance=Distance.DOT):
        """Create a new collection"""
        return self.client.create_collection(collection_name=name, vectors_config=VectorParams(size=vector_size, distance=distance))

    def insert_many(self, collection_name, points):
        """Insert multiple points with vectors and payloads"""
        return self.client.upsert(
            collection_name=collection_name, wait=True, points=[PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"]) for p in points]
        )

    def insert_one(self, collection_name, point):
        """Insert a single point"""
        return self.insert_many(collection_name, [point])

    def find(self, collection_name, query_vector, limit=3, with_payload=True):
        """Search for similar vectors"""
        return self.client.query_points(collection_name=collection_name, query=query_vector, with_payload=with_payload, limit=limit).points

    def find_one(self, collection_name, query_vector):
        """Find single most similar vector"""
        return self.find(collection_name, query_vector, limit=1)[0]

    def find_by_filter(self, collection_name, query_vector, filter_key, filter_value, limit=3):
        """Search with filter condition"""
        return self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=Filter(must=[FieldCondition(key=filter_key, match=MatchValue(value=filter_value))]),
            with_payload=True,
            limit=limit,
        ).points

    def delete_collection(self, name):
        """Delete a collection"""
        return self.client.delete_collection(collection_name=name)


# Example usage:
if __name__ == "__main__":
    # Initialize
    db = VectorDB()

    # Create collection
    db.create_collection("cities")

    # Insert data
    cities = [
        {"id": 1, "vector": [0.05, 0.61, 0.76, 0.74], "payload": {"city": "Berlin"}},
        {"id": 2, "vector": [0.19, 0.81, 0.75, 0.11], "payload": {"city": "London"}},
        {"id": 3, "vector": [0.36, 0.55, 0.47, 0.94], "payload": {"city": "Moscow"}},
    ]

    db.insert_many("cities", cities)

    # Search
    results = db.find("cities", [0.2, 0.1, 0.9, 0.7])
    print("Search results:", results)

    # Filtered search
    filtered = db.find_by_filter("cities", [0.2, 0.1, 0.9, 0.7], "city", "London")
    print("Filtered results:", filtered)
