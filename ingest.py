import os
import argparse

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from clean import clear_all_pdf, CHROMA_PDF_DIR

print("Loading environment variables...")
load_dotenv(".env")
# print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

# Parse command line arguments
parser = argparse.ArgumentParser(description="Ingest PDF files into ChromaDB")
parser.add_argument("--clear-pdf", action="store_true", help="Clear previous PDF data before ingesting")
args = parser.parse_args()

# Clear PDF data if requested
if args.clear_pdf:
    clear_all_pdf()
    print("Previous PDF data cleared.")
else:
    print("Keeping previous PDF data.")

embedding = OpenAIEmbeddings()

data_dir = "data"
all_docs = []

for file in os.listdir(data_dir):
    if file.endswith(".pdf"):
        loader = PyPDFLoader(os.path.join(data_dir, file))
        docs = loader.load()
        all_docs.extend(docs)

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(all_docs)

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "chroma")
CHROMA_PDF_DIR = os.path.join(CHROMA_PERSIST_DIR, "chroma_pdf")

pdf_db = Chroma.from_documents(
    documents=chunks,
    embedding=embedding,
    persist_directory=CHROMA_PDF_DIR
)

# pdf_db.persist()
print(f"✅ Saved {len(chunks)} PDF chunks.") 