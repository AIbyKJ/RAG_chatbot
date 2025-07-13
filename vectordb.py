from dotenv import load_dotenv
import os
import uuid
import time

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from userdb import get_user_pdfs

load_dotenv(".env")
embedding = OpenAIEmbeddings()
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)

CHAT_HISTORY_LIMIT = 10

PERSIST_DIR = os.getenv("PERSIST_DIR", ".\chroma")
CHROMA_MEMORY_DIR = os.path.join(PERSIST_DIR, "chroma_memory")
CHROMA_PDF_DIR = os.path.join(PERSIST_DIR, "chroma_pdf")


def insert_new_chunks(chunks):
    try:
        # Create a new Chroma instance or get existing one
        pdf_db = Chroma(
            persist_directory=CHROMA_PDF_DIR,
            embedding_function=embedding
        )
        
        # Add documents with proper metadata preservation
        pdf_db.add_documents(chunks)
        return True
    except Exception as e:
        print(f"Error inserting new chunks: {e}")
        return False




def save_user_message(user_id, message):
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

def retrieve_user_memory(user_id, query, k=3):
    persist_dir = CHROMA_MEMORY_DIR
    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=persist_dir
    )
    return db.similarity_search(query, k=k)

def get_all_history(user_id):
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

def clear_all_memory():
    collections = Chroma(persist_directory=CHROMA_MEMORY_DIR, embedding_function=None)._client.list_collections()
    for col in collections:
        db = Chroma(
            collection_name=col.name,
            embedding_function=embedding,
            persist_directory=CHROMA_MEMORY_DIR
        )
        db.delete_collection()

def clear_memory_by_user(user_id):
    """Delete memory for a specific user using the Chroma API (recommended)."""
    db = Chroma(
        collection_name=f"user_{user_id}",
        embedding_function=embedding,
        persist_directory=CHROMA_MEMORY_DIR
    )
    db.delete_collection()


def clear_all_pdf():
    collections = Chroma(persist_directory=CHROMA_PDF_DIR, embedding_function=None)._client.list_collections()
    for col in collections:
        db = Chroma(
            collection_name=col.name,
            embedding_function=embedding,
            persist_directory=CHROMA_PDF_DIR
        )
        db.delete_collection()


def clear_pdf_by_source(source_name):
    """Delete all PDF data for a specific source using Chroma API."""
    db = Chroma(
        persist_directory=CHROMA_PDF_DIR,
        embedding_function=embedding
    )
    
    # Get all documents and their metadata
    all_docs = db.get()
    
    if not all_docs["ids"]:
        return  # No documents to delete
    
    # Find documents with matching source
    ids_to_delete = []
    for i, metadata in enumerate(all_docs["metadatas"]):
        source_path = metadata.get("source")
        if source_path and os.path.basename(source_path) == source_name:
            ids_to_delete.append(all_docs["ids"][i])
    
    # Delete documents with matching source
    if ids_to_delete:
        db.delete(ids=ids_to_delete)
        print(f"Deleted {len(ids_to_delete)} documents from source: {source_name}")
    else:
        print(f"No documents found with source: {source_name}")

def get_available_user_ids():
    import re
    collections = Chroma(persist_directory=CHROMA_MEMORY_DIR, embedding_function=None)._client.list_collections()
    user_ids = []
    for col in collections:
        match = re.match(r"user_(.+)", col.name)
        if match:
            user_ids.append(match.group(1))
    return user_ids

def get_pdf_sources():
    db = Chroma(
        persist_directory=CHROMA_PDF_DIR,
        embedding_function=embedding
    )
    all_docs = db.get()
    sources = set()
    for meta in all_docs["metadatas"]:
        if "source" in meta:
            sources.add(meta["source"])
    return list(sources)

def retrieve_pdf_for_user(query, userid, k=3):
    """
    Retrieve the top-k most relevant PDF document chunks for a given query, but only from PDFs the user has access to (own + global).
    """
    user_pdfs = get_user_pdfs(userid)
    allowed_filenames = set(filename for _, filename in user_pdfs)
    db = Chroma(
        persist_directory=CHROMA_PDF_DIR,
        embedding_function=embedding
    )
    all_docs = db.get()
    # Filter docs by allowed filenames
    filtered_docs = []
    filtered_metadatas = []
    for i, meta in enumerate(all_docs["metadatas"]):
        source = meta.get("source")
        if source and os.path.basename(source) in allowed_filenames:
            filtered_docs.append(all_docs["documents"][i])
            filtered_metadatas.append(meta)
    if not filtered_docs:
        return []
    # Create a temporary Chroma collection for similarity search on filtered docs
    temp_db = Chroma.from_documents(filtered_docs, embedding=embedding)
    results = temp_db.similarity_search(query, k=k)
    return results
