from qdrant_client import QdrantClient

# Connect to Qdrant
client = QdrantClient("http://localhost:6333")

# Test connection
print("Qdrant is running!")
print(f"Collections: {client.get_collections()}")