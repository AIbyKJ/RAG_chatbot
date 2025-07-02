import os
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Use the same persist_directory as in your main app
persist_dir = "chroma/chroma_pdf"  # or "/mnt/azuredata/chroma_pdf" on Azure

print("Loading environment variables...")
load_dotenv(".env")
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

embedding = OpenAIEmbeddings()
db = Chroma(persist_directory=persist_dir, embedding_function=embedding)

query = "Do you know ott saito?"  # Change to something relevant to your PDFs
results = db.similarity_search(query, k=3)

print("Top 3 results for query:", query)
for i, doc in enumerate(results, 1):
    print(f"\nResult {i}:")
    print(doc.page_content)