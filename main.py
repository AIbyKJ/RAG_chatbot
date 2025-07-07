import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from memory import save_user_message, retrieve_user_memory, get_all_history
from clean import clear_all_pdf, clear_all_memory, clear_memory_by_user
import os

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
async def clear_all_memory_endpoint():
    """Clear all memory for all users."""
    try:
        await asyncio.to_thread(clear_all_memory)
        return {"message": "Memory cleared for all users."}
    except Exception as e:
        return {"error": f"Failed to clear all memory: {str(e)}"}

@app.delete("/memory/{user_id}")
async def clear_memory(user_id: str):
    """Clear all memory for a specific user."""
    try:
        await asyncio.to_thread(clear_memory_by_user, user_id)
        return {"message": f"Memory cleared for user {user_id}."}
    except Exception as e:
        return {"error": f"Failed to clear memory: {str(e)}"}
    
@app.delete("/pdf/{source_name}")
async def clear_pdf_by_source_endpoint(source_name: str):
    """Clear PDF data for a specific source name."""
    try:
        from clean import clear_pdf_by_source
        await asyncio.to_thread(clear_pdf_by_source, source_name, CHROMA_PDF_DIR)
        return {"message": f"PDF data cleared for source {source_name}."}
    except Exception as e:
        return {"error": f"Failed to clear PDF data for source {source_name}: {str(e)}"}

@app.delete("/pdf")
async def clear_all_pdf_endpoint():
    """Clear all PDF data."""
    try:
        await asyncio.to_thread(clear_all_pdf, CHROMA_PDF_DIR)
        return {"message": "All PDF data cleared."}
    except Exception as e:
        return {"error": f"Failed to clear all PDF data: {str(e)}"}

@app.post("/chat")
async def chat(req: ChatRequest):
    await asyncio.to_thread(save_user_message, req.user_id, req.message, persist_dir=CHROMA_MEMORY_DIR)
    mem_docs = await asyncio.to_thread(retrieve_user_memory, req.user_id, req.message, 3, CHROMA_MEMORY_DIR)
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

@app.get("/history/{user_id}")
async def get_history(user_id: str):
    docs = await asyncio.to_thread(get_all_history, user_id)
    return {"history": [doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in docs]}
