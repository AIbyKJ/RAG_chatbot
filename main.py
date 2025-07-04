import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from memory import save_user_message, retrieve_user_memory, clear_all_user_memory, clear_user_memory
import os
from clean import clear_all_pdf

load_dotenv()
app = FastAPI()
embedding = OpenAIEmbeddings()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma")
CHROMA_PDF_DIR = os.path.join(CHROMA_PERSIST_DIR, "chroma_pdf")
CHROMA_MEMORY_DIR = os.path.join(CHROMA_PERSIST_DIR, "chroma_memory")

pdf_db = Chroma(persist_directory=CHROMA_PDF_DIR, embedding_function=embedding)

llm = ChatOpenAI(model="gpt-4o", temperature=0)

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.delete("/memory")
async def clear_all_memory():
    """Clear all memory for all users."""
    try:
        await asyncio.to_thread(clear_all_user_memory)
        return {"message": "Memory cleared for all users."}
    except Exception as e:
        return {"error": f"Failed to clear all memory: {str(e)}"}

@app.delete("/memory/{user_id}")
async def clear_memory(user_id: str):
    """Clear all memory for a specific user."""
    try:
        await asyncio.to_thread(clear_user_memory, user_id)
        return {"message": f"Memory cleared for user {user_id}."}
    except Exception as e:
        return {"error": f"Failed to clear memory: {str(e)}"}

@app.post("/chat")
async def chat(req: ChatRequest):
    await asyncio.to_thread(save_user_message, req.user_id, req.message, persist_dir=CHROMA_MEMORY_DIR)
    mem_docs = await asyncio.to_thread(retrieve_user_memory, req.user_id, req.message, 7, CHROMA_MEMORY_DIR)
    pdf_docs = await asyncio.to_thread(pdf_db.similarity_search, req.message, k=3)

    mem_text = "\n".join([d.page_content for d in mem_docs]) if mem_docs else "No previous conversation found."
    pdf_text = "\n".join([d.page_content for d in pdf_docs]) if pdf_docs else "No relevant documents found."

    prompt = f"""
    Previous conversation:
    {mem_text}

    Relevant documents:
    {pdf_text}

    User: {req.message}
    Answer:
    """

    print("*"*10, prompt, "*"*10)
    response = await asyncio.to_thread(llm.predict, prompt)
    return {"response": response, "prompt": prompt}

@app.delete("/pdf")
async def clear_all_pdf_endpoint():
    """Clear all PDF data (global)."""
    try:
        await asyncio.to_thread(clear_all_pdf)
        return {"message": "All PDF data cleared."}
    except Exception as e:
        return {"error": f"Failed to clear PDF data: {str(e)}"}
