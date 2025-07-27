from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import threading
import subprocess
from RAG import RAGSystem

app = Flask(__name__)
CORS(app)

# Global RAG system instance
rag_system = None

def initialize_rag_system():
    global rag_system
    try:
        rag_system = RAGSystem()
        rag_system.initialize_qa_system()
        print("✅ RAG System initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        raise

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
        
        if rag_system is None:
            return jsonify({'error': 'RAG system not initialized'}), 500
        
        # Get response from RAG system
        result = rag_system.ask_question(question)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    try:
        if rag_system:
            rag_system.clear_conversation()
        return jsonify({'message': 'Conversation cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_documents():
    def run_indexing():
        try:
            # Create a new RAG system instance for indexing
            indexing_rag = RAGSystem()
            success = indexing_rag.run_indexing_workflow()
            if success:
                print('✅ Document indexing completed successfully!')
            else:
                print('❌ Document indexing failed or was cancelled')
        except Exception as e:
            print(f'❌ Indexing failed: {e}')

    threading.Thread(target=run_indexing).start()
    return jsonify({'status': 'Indexing started'}), 202

if __name__ == '__main__':
    try:
        initialize_rag_system()
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        print("Make sure Qdrant is running and API keys are set in .env file")