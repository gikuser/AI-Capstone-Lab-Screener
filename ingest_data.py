import os
from rag_pipeline import build_vector_index

def main():
    \"\"\"
    Ingests HR guidelines from text files and builds the FAISS index.
    In a real production system, this would also process PDF/Word docs.
    \"\"\"
    print("--- Starting Data Ingestion ---")
    try:
        build_vector_index()
        print("✅ Data Ingestion Successful! FAISS index created.")
    except Exception as e:
        print(f"❌ Ingestion Failed: {str(e)}")

if __name__ == "__main__":
    main()
