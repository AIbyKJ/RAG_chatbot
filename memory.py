from dotenv import load_dotenv
import os
import uuid
import time

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv(".env")
embedding = OpenAIEmbeddings()
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)

CHAT_HISTORY_LIMIT = 10

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "chroma")
CHROMA_MEMORY_DIR = os.path.join(CHROMA_PERSIST_DIR, "chroma_memory")

def save_user_message(user_id, message, persist_dir=None):
    if persist_dir is None:
        persist_dir = CHROMA_MEMORY_DIR
    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=persist_dir
    )
    # Fetch all existing messages
    all_docs = db.get()
    all_ids = all_docs["ids"]
    all_metadatas = all_docs["metadatas"]
    # Sort by timestamp (if present), else keep as is
    docs_with_time = []
    for idx, meta in enumerate(all_metadatas):
        ts = meta.get("timestamp", 0)
        docs_with_time.append((all_ids[idx], ts))
    docs_with_time.sort(key=lambda x: x[1])  # oldest first
    # If at or above limit, delete oldest so only (limit-1) remain
    if len(docs_with_time) >= CHAT_HISTORY_LIMIT:
        num_to_delete = len(docs_with_time) - (CHAT_HISTORY_LIMIT - 1)
        ids_to_delete = [doc[0] for doc in docs_with_time[:num_to_delete]]
        db.delete(ids=ids_to_delete)
    # Prepare new chunk(s) with timestamp
    chunks = splitter.create_documents([message])
    now = time.time()
    for c in chunks:
        c.metadata["user_id"] = user_id
        c.metadata["timestamp"] = now
    ids = [str(uuid.uuid4()) for _ in chunks]
    db.add_documents(chunks, ids=ids)
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

def get_all_history(user_id, persist_dir=None):
    if persist_dir is None:
        persist_dir = CHROMA_MEMORY_DIR
    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=persist_dir
    )
    all_docs = db.get()
    docs = []
    for i, doc in enumerate(all_docs["documents"]):
        meta = all_docs["metadatas"][i]
        ts = meta.get("timestamp", 0)
        docs.append((ts, doc))
    docs.sort(key=lambda x: x[0])  # oldest to newest
    return [doc for ts, doc in docs]
