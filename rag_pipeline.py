import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Define paths
current_dir = os.path.dirname(os.path.abspath(__file__))
KB_FILE_PATH = os.path.join(current_dir, "hr_guidelines.txt")
FAISS_INDEX_DIR = os.path.join(current_dir, "faiss_index")

# Initialize embeddings model
# Using a lightweight local embedding model so we don't need additional API keys
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def build_vector_index():
    \"\"\"Reads the HR guidelines, chunks them, and builds a FAISS vector database.\"\"\"
    print("Building RAG Vector Index...")
    if not os.path.exists(KB_FILE_PATH):
        raise FileNotFoundError(f"Knowledge base file not found at: {KB_FILE_PATH}")

    loader = TextLoader(KB_FILE_PATH)
    documents = loader.load()

    # Chunk the document
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        add_start_index=True
    )
    chunks = text_splitter.split_documents(documents)

    # Build FAISS vector store
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # Save it locally so we don't have to rebuild it every time
    vectorstore.save_local(FAISS_INDEX_DIR)
    print(f"Vector Index built and saved to {FAISS_INDEX_DIR}")
    return vectorstore

def get_vector_store():
    \"\"\"Loads the FAISS index if it exists, otherwise builds it.\"\"\"
    if os.path.exists(FAISS_INDEX_DIR):
        # Load existing index
        try:
            return FAISS.load_local(FAISS_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            print(f"Failed to load existing index: {e}. Rebuilding...")
            return build_vector_index()
    else:
        return build_vector_index()

def search_knowledge_base(query: str, k: int = 2) -> str:
    \"\"\"Retrieves relevant context from the HR knowledge base.\"\"\"
    # Ensure vector store is available
    vectorstore = get_vector_store()
    
    # Perform similarity search
    results = vectorstore.similarity_search(query, k=k)
    
    if not results:
        return "No relevant HR guidelines found."
    
    # Combine retrieved text
    context = "\n\n".join([f"Guideline Excerpt:\n{doc.page_content}" for doc in results])
    return context

if __name__ == "__main__":
    # Test the RAG pipeline standalone
    print("Testing RAG Pipeline...")
    query = "What are the rules for Senior machine learning engineers?"
    res = search_knowledge_base(query)
    print(f"\nQUERY: {query}")
    print(f"\nRESULT:\n{res}")
