from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from langchain_nomic import NomicEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from qdrant_client import QdrantClient

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Global variables for the QA chain
qa_chain = None
memory = None

def initialize_qa_system():
    global qa_chain, memory
    
    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    nomic_api_key = os.getenv("NOMIC_API_KEY")
    
    if not openai_key or not nomic_api_key:
        raise ValueError("Missing API keys in environment variables")
    
    # Connect to Qdrant
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)
    
    # Initialize embeddings
    embedding_model = NomicEmbeddings(
        model="nomic-embed-text-v1.5",
        nomic_api_key=nomic_api_key
    )
    
    # Create vector store
    vector_store = QdrantVectorStore(
        client=client,
        collection_name="bank_documents",
        embedding=embedding_model
    )
    
    # Initialize LLM
    llm = ChatOpenAI(
        openai_api_key=openai_key,
        model_name="gpt-4",
        temperature=0
    )
    
    # Initialize memory with output key specified
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    
    # Create QA chain
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
        memory=memory,
        return_source_documents=True,
        chain_type="stuff"
    )
    
    print("✅ QA System initialized successfully!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        if qa_chain is None:
            return jsonify({'error': 'QA system not initialized'}), 500
        
        # Get response from QA chain
        result = qa_chain({
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
                import os
                doc_name = os.path.basename(source_path)
            else:
                doc_name = 'Unknown'
            
            source_info = {
                'source': doc_name,
                'page': doc.metadata.get('page', 'N/A')
            }
            sources.append(source_info)
        
        return jsonify({
            'answer': answer,
            'sources': sources,
            'question': question
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    global memory
    try:
        if memory:
            memory.clear()
        return jsonify({'message': 'Conversation cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        initialize_qa_system()
        # Get port from environment variable or default to 5000
        port = int(os.getenv('PORT', 5000))
        # Run on all interfaces for Docker compatibility
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        print("Make sure Qdrant is running and API keys are set in .env file")