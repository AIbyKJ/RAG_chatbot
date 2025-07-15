import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
<<<<<<< HEAD:utils/ingest.py
from utils.vectordb import clear_all_pdf, insert_new_chunks
=======
from vectordb import clear_all_pdf, insert_new_chunks
from userdb import get_all_users
>>>>>>> 3578a32f7d0fa3879920ea6a704e04ffd97717f7:ingest.py

print("Loading environment variables...")
load_dotenv(".env")

embedding = OpenAIEmbeddings()

PERSIST_DIR = os.getenv("PERSIST_DIR", "")
DATA_DIR = os.path.join(PERSIST_DIR, "data")
# DATA_DIR = "data"

def user_exists(userid: str) -> bool:
    users = get_all_users()
    return any(u[0] == userid for u in users)

def get_available_pdfs():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    pdfs = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.pdf')]
    print("Available PDFs:", pdfs)
    return pdfs

def ingest_all_pdfs(clear_pdf: bool = False, user_id: str = None):
    os.makedirs(DATA_DIR, exist_ok=True)
    if user_id and not user_exists(user_id):
        print(f"User {user_id} does not exist. Skipping ingestion.")
        return {"ingested_files": [], "chunks": 0, "success": False, "warning": f"User {user_id} does not exist."}
    if clear_pdf:
        clear_all_pdf()
        print("Previous PDF data cleared.")
    else:
        print("Keeping previous PDF data.")
    # Get user's accessible PDFs if user_id is provided
    if user_id:
        from userdb import get_user_pdfs
        user_pdfs = get_user_pdfs(user_id)
        allowed_filenames = set(filename for _, filename in user_pdfs)
        print(f"Ingesting PDFs accessible to user {user_id}: {allowed_filenames}")
    else:
        allowed_filenames = None
        print("Ingesting all PDFs (admin mode)")
    all_docs = []
    ingested_files = []
    # Ingest PDFs from correct folders using relative paths
    if user_id:
        # Ingest user's own PDFs
        user_folder = os.path.join(DATA_DIR, user_id)
        if os.path.isdir(user_folder):
            for file in os.listdir(user_folder):
                if file.lower().endswith(".pdf"):
                    rel_path = os.path.join(user_id, file)
                    if allowed_filenames and rel_path not in allowed_filenames:
                        print(f"Skipping {rel_path} - not accessible to user {user_id}")
                        continue
                    try:
                        loader = PyPDFLoader(os.path.join(DATA_DIR, rel_path))
                        docs = loader.load()
                        all_docs.extend(docs)
                        ingested_files.append(rel_path)
                    except Exception as e:
                        print(f"Error processing {rel_path}: {e}")
                        continue
        # Ingest public PDFs
        public_folder = os.path.join(DATA_DIR, "public")
        if os.path.isdir(public_folder):
            for file in os.listdir(public_folder):
                if file.lower().endswith(".pdf"):
                    rel_path = os.path.join("public", file)
                    if allowed_filenames and rel_path not in allowed_filenames:
                        print(f"Skipping {rel_path} - not accessible to user {user_id}")
                        continue
                    try:
                        loader = PyPDFLoader(os.path.join(DATA_DIR, rel_path))
                        docs = loader.load()
                        all_docs.extend(docs)
                        ingested_files.append(rel_path)
                    except Exception as e:
                        print(f"Error processing {rel_path}: {e}")
                        continue
    else:
        # Ingest all PDFs in all user and public folders
        for folder in os.listdir(DATA_DIR):
            folder_path = os.path.join(DATA_DIR, folder)
            if not os.path.isdir(folder_path):
                continue
            for file in os.listdir(folder_path):
                if file.lower().endswith(".pdf"):
                    rel_path = os.path.join(folder, file)
                    try:
                        loader = PyPDFLoader(os.path.join(DATA_DIR, rel_path))
                        docs = loader.load()
                        all_docs.extend(docs)
                        ingested_files.append(rel_path)
                    except Exception as e:
                        print(f"Error processing {rel_path}: {e}")
                        continue
    if not all_docs:
        print("⚠️ No documents to ingest.")
        return {"ingested_files": ingested_files, "chunks": 0, "success": False, "warning": "No documents to ingest."}
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    try:
        chunks = splitter.split_documents(all_docs)
        if not chunks:
            print("⚠️ No chunks to ingest. Skipping insertion.")
            return {"ingested_files": ingested_files, "chunks": 0, "success": False, "warning": "No chunks to ingest."}
        success = insert_new_chunks(chunks)
        return {"ingested_files": ingested_files, "chunks": len(chunks), "success": success}
    except Exception as e:
        print(f"Error splitting/ingesting documents: {e}")
        return {"ingested_files": ingested_files, "chunks": 0, "success": False, "error": str(e)}

def ingest_one_pdf(filename: str, user_id: str = None):
    os.makedirs(DATA_DIR, exist_ok=True)
    
    """Ingest a single PDF file by filename in the data/data directory."""
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(file_path) or not filename.lower().endswith(".pdf"):
        print("File not found or not a PDF.")
        return {"error": "File not found or not a PDF."}
    
    # Check if user has access to this PDF
    if user_id:
        from userdb import get_user_pdfs
        user_pdfs = get_user_pdfs(user_id)
        allowed_filenames = set(filename for _, filename in user_pdfs)
        if filename not in allowed_filenames:
            print(f"User {user_id} does not have access to {filename}")
            return {"error": f"User {user_id} does not have access to {filename}"}
    
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    if not chunks:
        print(f"⚠️ No chunks to ingest for {filename}. Skipping insertion.")
        return {"ingested_file": filename, "chunks": 0, "success": False, "warning": "No chunks to ingest."}
    success = insert_new_chunks(chunks)
    print(f"✅ Saved {len(chunks)} PDF chunks from {filename}.")
    return {"ingested_file": filename, "chunks": len(chunks), "success": success}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest PDF files into ChromaDB")
    parser.add_argument("--clear-pdf", action="store_true", help="Clear previous PDF data before ingesting")
    args = parser.parse_args()
    ingest_all_pdfs(clear_pdf=args.clear_pdf) 