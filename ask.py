import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from langchain_nomic import NomicEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from qdrant_client import QdrantClient

# === Step 1: Load Environment Variables ===
def load_api_keys():
    load_dotenv()
    return os.getenv("OPENAI_API_KEY")

# === Step 2: Connect to Qdrant ===
def connect_to_qdrant(collection_name):
    client = QdrantClient(url="http://localhost:6333")
    nomic_api_key = os.getenv("NOMIC_API_KEY")
    if not nomic_api_key:
        raise ValueError("NOMIC_API_KEY not found in environment variables. Please check your .env file.")
    
    embedding_model = NomicEmbeddings(
        model="nomic-embed-text-v1.5",
        nomic_api_key=nomic_api_key
    )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embedding_model
    )

    return vector_store

# === Step 3: Create Conversational Chain ===
def create_qa_chain(vector_store, openai_key):
    llm = ChatOpenAI(
        openai_api_key=openai_key,
        model_name="gpt-4",
        temperature=0
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
        memory=memory,
        return_source_documents=False,
        chain_type="stuff"
    )

    return chain

# === Step 4: Ask Question in a Loop ===
def start_chat(chain):
    print("💬 You can now ask questions. Type 'exit' to quit.\n")

    while True:
        user_question = input("You: ")

        if user_question.lower() == "exit":
            print("👋 Goodbye!")
            break

        result = chain.run(
            question=f"Answer strictly based on the documents. If answer is not available, say 'Not found in context.Also never say anything out of context or anything extra.Just answer according to the Sources nothing else.'\n\n{user_question}"
        )

        print(f"\nAssistant: {result}\n")

# === Main Function ===
def main():
    print("🔧 Loading API key and connecting to vector DB...")
    openai_key = load_api_keys()
    collection_name = "bank_documents"

    vector_store = connect_to_qdrant(collection_name)
    qa_chain = create_qa_chain(vector_store, openai_key)

    start_chat(qa_chain)

if __name__ == "__main__":
    main()
