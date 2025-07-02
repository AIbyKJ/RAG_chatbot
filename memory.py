from dotenv import load_dotenv
import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv(".env")
embedding = OpenAIEmbeddings()
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "chroma")
CHROMA_MEMORY_DIR = os.path.join(CHROMA_PERSIST_DIR, "chroma_memory")

def save_user_message(user_id, message, persist_dir=None):
    if persist_dir is None:
        persist_dir = CHROMA_MEMORY_DIR
    chunks = splitter.create_documents([message])
    for c in chunks:
        c.metadata["user_id"] = user_id

    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=persist_dir
    )
    db.add_documents(chunks)
    # db.persist()

def retrieve_user_memory(user_id, query, k=3, persist_dir=None):
    if persist_dir is None:
        persist_dir = CHROMA_MEMORY_DIR
    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=persist_dir
    )
    return db.similarity_search(query, k=k)


def clear_user_memory(user_id, persist_dir="chroma/chroma_memory"):
    """Clear all memory for a specific user"""
    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=persist_dir
    )
    db.delete_collection()
    
def clear_all_user_memory(persist_dir="chroma/chroma_memory"):
    """Clear all memory for all users"""
    import os
    import shutil
    
    # Remove the entire persist directory to clear all collections
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
        os.makedirs(persist_dir, exist_ok=True)
