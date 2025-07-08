from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "chroma")
CHROMA_MEMORY_DIR = os.path.join(CHROMA_PERSIST_DIR, "chroma_memory")
CHROMA_PDF_DIR = os.path.join(CHROMA_PERSIST_DIR, "chroma_pdf")

embedding = OpenAIEmbeddings()

def clear_all_memory():
    """Delete all user memory (removes chroma_memory directory and recreates it)."""
    import shutil
    if os.path.exists(CHROMA_MEMORY_DIR):
        shutil.rmtree(CHROMA_MEMORY_DIR)
    os.makedirs(CHROMA_MEMORY_DIR, exist_ok=True)


def clear_memory_by_user(user_id):
    """Delete memory for a specific user using the Chroma API (recommended)."""
    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=CHROMA_MEMORY_DIR
    )
    db.delete_collection()


def clear_all_pdf(persist_dir=CHROMA_PDF_DIR):
    """Delete all PDF data using Chroma API (removes all collections and files in chroma_pdf)."""
    import shutil
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
    os.makedirs(persist_dir, exist_ok=True)
    # Optionally, you could also use Chroma's delete_collection if you use named collections for PDFs


def clear_pdf_by_source(source_name, persist_dir=CHROMA_PDF_DIR):
    """Delete all PDF data for a specific source using Chroma API."""
    db = Chroma(
        persist_directory=persist_dir,
        embedding_function=embedding
    )
    
    # Get all documents and their metadata
    all_docs = db.get()
    
    if not all_docs["ids"]:
        return  # No documents to delete
    
    # Find documents with matching source
    ids_to_delete = []
    for i, metadata in enumerate(all_docs["metadatas"]):
        if metadata.get("source") == source_name:
            ids_to_delete.append(all_docs["ids"][i])
    
    # Delete documents with matching source
    if ids_to_delete:
        db.delete(ids=ids_to_delete)
        print(f"Deleted {len(ids_to_delete)} documents from source: {source_name}")
    else:
        print(f"No documents found with source: {source_name}")
