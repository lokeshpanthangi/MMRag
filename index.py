import os
import tkinter as tk
from tkinter import filedialog, messagebox
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


# === Step 1: Select and Load Files ===
def select_files():
    """Use tkinter file dialog to select PDF and TXT files"""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    # Configure file dialog
    file_types = [
        ('All supported files', '*.pdf;*.txt'),
        ('PDF files', '*.pdf'),
        ('Text files', '*.txt'),
        ('All files', '*.*')
    ]
    
    selected_files = filedialog.askopenfilenames(
        title="Select PDF and TXT files to index",
        filetypes=file_types
    )
    
    root.destroy()
    
    if not selected_files:
        messagebox.showinfo("No files selected", "No files were selected. Exiting...")
        return None
    
    return list(selected_files)

def load_documents_from_files(file_paths):
    """Load documents from selected file paths"""
    all_docs = []
    
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        
        if file_name.lower().endswith(".pdf"):
            print(f"Loading PDF: {file_name}")
            try:
                loader = PyPDFLoader(file_path)
                pages = loader.load_and_split()
                all_docs.extend(pages)
            except Exception as e:
                print(f"Error loading PDF {file_name}: {e}")
                
        elif file_name.lower().endswith(".txt"):
            print(f"Loading TXT: {file_name}")
            try:
                loader = TextLoader(file_path, encoding='utf-8')
                documents = loader.load()
                all_docs.extend(documents)
            except Exception as e:
                print(f"Error loading TXT {file_name}: {e}")
        else:
            print(f"Skipping unsupported file: {file_name}")
    
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
    print("=== RAG Document Indexer ===")
    print("Please select PDF and TXT files to index...")
    
    # Step 1: Select files using file dialog
    selected_files = select_files()
    if not selected_files:
        return
    
    print(f"Selected {len(selected_files)} file(s):")
    for file_path in selected_files:
        print(f"  - {os.path.basename(file_path)}")
    
    print("\nStep 1: Loading documents...")
    documents = load_documents_from_files(selected_files)
    
    if not documents:
        print("No documents were loaded successfully. Exiting...")
        return
    
    print(f"Loaded {len(documents)} document(s)")

    print("\nStep 2: Chunking documents...")
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunks")

    print("\nStep 3: Connecting to Qdrant...")
    qdrant_client, collection_name = connect_qdrant()

    print("\nStep 4: Initializing embedding model...")
    embedding_model = get_nomic_embedding_model()

    print("\nStep 5: Indexing documents...")
    index_documents(chunks, embedding_model, qdrant_client, collection_name)
    
    print("\n✅ Document indexing completed successfully!")

if __name__ == "__main__":
    main()
