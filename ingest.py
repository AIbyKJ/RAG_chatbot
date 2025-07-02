import os

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

print("Loading environment variables...")
load_dotenv(".env")
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

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

pdf_db = Chroma.from_documents(
    documents=chunks,
    embedding=embedding,
    persist_directory="chroma/chroma_pdf"
)

# pdf_db.persist()
print(f"✅ Saved {len(chunks)} PDF chunks.") 