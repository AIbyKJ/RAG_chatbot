from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from memory import clear_user_memory

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
    clear_user_memory(user_id, persist_dir=CHROMA_MEMORY_DIR)


def clear_all_pdf(persist_dir=CHROMA_PDF_DIR):
    """Delete all PDF data using Chroma API (removes all collections and files in chroma_pdf)."""
    import shutil
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
    os.makedirs(persist_dir, exist_ok=True)
    # Optionally, you could also use Chroma's delete_collection if you use named collections for PDFs
