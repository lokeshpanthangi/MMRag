import os
import tkinter as tk
from tkinter import filedialog, messagebox
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nomic import NomicEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from uuid import uuid4

class RAGSystem:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize variables
        self.client = None
        self.collection_name = "bank_documents"
        self.embedding_model = None
        self.vector_store = None
        self.qa_chain = None
        self.memory = None
        
        # Validate API keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.nomic_api_key = os.getenv("NOMIC_API_KEY")
        
        if not self.openai_key or not self.nomic_api_key:
            raise ValueError("Missing API keys in environment variables. Please check your .env file.")
    
    def initialize_embedding_model(self):
        """Initialize the Nomic embedding model"""
        self.embedding_model = NomicEmbeddings(
            model="nomic-embed-text-v1.5",
            nomic_api_key=self.nomic_api_key
        )
        return self.embedding_model
    
    def connect_qdrant(self):
        """Connect to Qdrant and create collection if needed"""
        self.client = QdrantClient(url="http://localhost:6333")
        
        # Create collection if it doesn't exist
        try:
            self.client.get_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' already exists.")
        except Exception:
            print(f"Creating collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
        
        return self.client
    
    def select_files(self):
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
            print("No files were selected.")
            return None
        
        return list(selected_files)
    
    def load_documents_from_files(self, file_paths):
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
    
    def chunk_documents(self, documents, chunk_size=500, chunk_overlap=50):
        """Split documents into chunks"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " "]
        )
        
        chunks = splitter.split_documents(documents)
        return chunks
    
    def index_documents(self, chunks):
        """Index and store chunks in Qdrant"""
        if not self.embedding_model:
            self.initialize_embedding_model()
        
        if not self.client:
            self.connect_qdrant()
        
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
        
        # Create vector store
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embedding_model
        )
        
        print("Uploading to Qdrant...")
        self.vector_store.add_texts(texts=texts, metadatas=metadatas)
        print(f"✅ Indexed {len(texts)} chunks into Qdrant.")
    
    def initialize_qa_system(self):
        """Initialize the QA system for querying"""
        if not self.embedding_model:
            self.initialize_embedding_model()
        
        if not self.client:
            self.connect_qdrant()
        
        # Create vector store
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embedding_model
        )
        
        # Initialize LLM
        llm = ChatOpenAI(
            openai_api_key=self.openai_key,
            model_name="gpt-4",
            temperature=0.2
        )
        
        # Initialize memory with output key specified
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Create QA chain
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            memory=self.memory,
            return_source_documents=True,
            chain_type="stuff"
        )
        
        print("✅ QA System initialized successfully!")
    
    def ask_question(self, question):
        """Ask a question and get response with sources"""
        if not self.qa_chain:
            self.initialize_qa_system()
        
        result = self.qa_chain({
            "question": f"Answer strictly based on the documents. If answer is not available, say 'Not found in context.'\n\n{question}"
        })
        
        # Extract answer and sources
        answer = result.get('answer', 'No answer generated')
        source_docs = result.get('source_documents', [])
        
        # Format sources - extract only document names
        sources = []
        for doc in source_docs:
            source_path = doc.metadata.get('source', 'Unknown')
            # Extract just the filename from the full path
            if source_path != 'Unknown':
                doc_name = os.path.basename(source_path)
            else:
                doc_name = 'Unknown'
            
            source_info = {
                'source': doc_name,
                'page': doc.metadata.get('page', 'N/A')
            }
            sources.append(source_info)
        
        return {
            'answer': answer,
            'sources': sources,
            'question': question
        }
    
    def clear_conversation(self):
        """Clear conversation memory"""
        if self.memory:
            self.memory.clear()
            print("Conversation cleared.")
    
    def run_indexing_workflow(self):
        """Run the complete indexing workflow with file selection"""
        print("=== RAG Document Indexer ===")
        print("Please select PDF and TXT files to index...")
        
        # Step 1: Select files using file dialog
        selected_files = self.select_files()
        if not selected_files:
            return False
        
        print(f"Selected {len(selected_files)} file(s):")
        for file_path in selected_files:
            print(f"  - {os.path.basename(file_path)}")
        
        print("\nStep 1: Loading documents...")
        documents = self.load_documents_from_files(selected_files)
        
        if not documents:
            print("No documents were loaded successfully.")
            return False
        
        print(f"Loaded {len(documents)} document(s)")
        
        print("\nStep 2: Chunking documents...")
        chunks = self.chunk_documents(documents)
        print(f"Created {len(chunks)} chunks")
        
        print("\nStep 3: Connecting to Qdrant...")
        self.connect_qdrant()
        
        print("\nStep 4: Initializing embedding model...")
        self.initialize_embedding_model()
        
        print("\nStep 5: Indexing documents...")
        self.index_documents(chunks)
        
        print("\n✅ Document indexing completed successfully!")
        return True
    
    def run_interactive_chat(self):
        """Run interactive chat session"""
        print("\n=== RAG Interactive Chat ===")
        print("Initializing QA system...")
        
        try:
            self.initialize_qa_system()
        except Exception as e:
            print(f"Failed to initialize QA system: {e}")
            return
        
        print("💬 You can now ask questions. Type 'exit' to quit.\n")
        
        while True:
            user_question = input("You: ")
            
            if user_question.lower() == "exit":
                print("👋 Goodbye!")
                break
            
            try:
                result = self.ask_question(user_question)
                print(f"\nAssistant: {result['answer']}")
                
                if result['sources']:
                    print("\n📚 Sources:")
                    for source in result['sources']:
                        page_info = f" (Page {source['page']})" if source['page'] != 'N/A' else ""
                        print(f"  📄 {source['source']}{page_info}")
                
                print()
                
            except Exception as e:
                print(f"\nError: {e}\n")

# Convenience functions for backward compatibility
def run_indexing():
    """Run document indexing workflow"""
    rag = RAGSystem()
    return rag.run_indexing_workflow()

def run_chat():
    """Run interactive chat"""
    rag = RAGSystem()
    rag.run_interactive_chat()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "index":
            run_indexing()
        elif sys.argv[1] == "chat":
            run_chat()
        else:
            print("Usage: python RAG.py [index|chat]")
    else:
        # Default behavior - show menu
        print("=== RAG System ===")
        print("1. Index documents")
        print("2. Start chat")
        choice = input("Choose an option (1 or 2): ")
        
        if choice == "1":
            run_indexing()
        elif choice == "2":
            run_chat()
        else:
            print("Invalid choice.")