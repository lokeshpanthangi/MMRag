import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nomic import NomicEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from uuid import uuid4

# Load environment variables
load_dotenv()


# === Step 1: Load PDFs and TXT files ===
def load_documents_from_folder(folder_path):
    all_docs = []
    file_names = os.listdir(folder_path)

    for file_name in file_names:
        file_path = os.path.join(folder_path, file_name)

        if file_name.lower().endswith(".pdf"):
            print(f"Loading PDF: {file_name}")
            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
            all_docs.extend(pages)
        elif file_name.lower().endswith(".txt"):
            print(f"Loading TXT: {file_name}")
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            all_docs.extend(documents)

    return all_docs

# === Step 2: Chunk the Documents ===
def chunk_documents(documents, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "]
    )

    chunks = splitter.split_documents(documents)
    return chunks

# === Step 3: Initialize Embedding Model ===
def get_nomic_embedding_model():
    nomic_api_key = os.getenv("NOMIC_API_KEY")
    if not nomic_api_key:
        raise ValueError("NOMIC_API_KEY not found in environment variables. Please check your .env file.")
    
    return NomicEmbeddings(
        model="nomic-embed-text-v1.5",
        nomic_api_key=nomic_api_key
    )

# === Step 4: Connect to Qdrant DB ===
def connect_qdrant():
    client = QdrantClient(
        url="http://localhost:6333"  # Change this if using cloud Qdrant
    )

    collection_name = "bank_documents"

    # Create collection if it doesn't exist
    try:
        client.get_collection(collection_name)
        print(f"Collection '{collection_name}' already exists.")
    except Exception:
        print(f"Creating collection '{collection_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )

    return client, collection_name

# === Step 5: Index and Store Chunks in Qdrant ===
def index_documents(chunks, embedding_model, qdrant_client, collection_name):
    texts = []
    metadatas = []

    for chunk in chunks:
        texts.append(chunk.page_content)

        metadata = {
            "source": chunk.metadata.get("source", ""),
            "page": chunk.metadata.get("page", -1),
            "chunk_id": str(uuid4())
        }

        metadatas.append(metadata)

    print("Generating embeddings...")
    embeddings = embedding_model.embed_documents(texts)

    print("Uploading to Qdrant...")
    qdrant = QdrantVectorStore(
        client=qdrant_client,
        collection_name=collection_name,
        embedding=embedding_model
    )

    qdrant.add_texts(texts=texts, metadatas=metadatas)
    print(f"✅ Indexed {len(texts)} chunks into Qdrant.")

# === Main Entry Point ===
def main():
    folder_path = "docs"  # Folder where PDFs and TXT files are stored

    print("Step 1: Loading documents...")
    documents = load_documents_from_folder(folder_path)

    print("Step 2: Chunking documents...")
    chunks = chunk_documents(documents)

    print("Step 3: Connecting to Qdrant...")
    qdrant_client, collection_name = connect_qdrant()

    print("Step 4: Initializing embedding model...")
    embedding_model = get_nomic_embedding_model()

    print("Step 5: Indexing documents...")
    index_documents(chunks, embedding_model, qdrant_client, collection_name)

if __name__ == "__main__":
    main()
