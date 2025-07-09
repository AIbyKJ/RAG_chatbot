import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from vectordb import clear_all_pdf, insert_new_chunks

print("Loading environment variables...")
load_dotenv(".env")

embedding = OpenAIEmbeddings()

PERSIST_DIR = os.getenv("PERSIST_DIR", "")
DATA_DIR = os.path.join(PERSIST_DIR, "data")
# DATA_DIR = "data"


def get_available_pdfs():
    pdfs = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.pdf')]
    print("Available PDFs:", pdfs)
    return pdfs

def ingest_all_pdfs(clear_pdf: bool = False):
    """Ingest all PDF files in the data/data directory."""
    if clear_pdf:
        clear_all_pdf()
        print("Previous PDF data cleared.")
    else:
        print("Keeping previous PDF data.")
    all_docs = []
    for file in os.listdir(DATA_DIR):
        if file.lower().endswith(".pdf"):
            try:
                loader = PyPDFLoader(os.path.join(DATA_DIR, file))
                docs = loader.load()
                all_docs.extend(docs)
            except Exception as e:
                print(f"Error processing {file}: {e}")
                continue
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    try:
        chunks = splitter.split_documents(all_docs)
        success = insert_new_chunks(chunks)
        print(f"✅ Saved {len(chunks)} PDF chunks.")
        return {"ingested_files": [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.pdf')], "chunks": len(chunks), "success": success}
    except Exception as e:
        print(f"Error during chunking or insertion: {e}")
        return {"error": str(e)}

def ingest_one_pdf(filename: str):
    """Ingest a single PDF file by filename in the data/data directory."""
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(file_path) or not filename.lower().endswith(".pdf"):
        print("File not found or not a PDF.")
        return {"error": "File not found or not a PDF."}
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    success = insert_new_chunks(chunks)
    print(f"✅ Saved {len(chunks)} PDF chunks from {filename}.")
    return {"ingested_file": filename, "chunks": len(chunks), "success": success}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest PDF files into ChromaDB")
    parser.add_argument("--clear-pdf", action="store_true", help="Clear previous PDF data before ingesting")
    args = parser.parse_args()
    ingest_all_pdfs(clear_pdf=args.clear_pdf) 