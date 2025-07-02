import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from memory import save_user_message, retrieve_user_memory
import os

load_dotenv()
app = FastAPI()
embedding = OpenAIEmbeddings()

pdf_db = Chroma(persist_directory="./chroma/chroma_pdf", embedding_function=embedding)

print(os.getenv("FAKE_LLM"))
# Fake LLM for testing
if bool(os.getenv("FAKE_LLM")):
    class DummyLLM:
        def predict(self, prompt):
            return "dummy response"
    llm = DummyLLM()
else:
    llm = ChatOpenAI(model="gpt-4", temperature=0)

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.delete("/memory")
async def clear_all_memory():
    """Clear all memory for all users"""
    try:
        # Import here to avoid circular imports
        from memory import clear_all_user_memory
        await asyncio.to_thread(clear_all_user_memory, "./chroma/chroma_memory")
        return {"message": "Memory cleared for all users"}
    except Exception as e:
        return {"error": f"Failed to clear all memory: {str(e)}"}



@app.delete("/memory/{user_id}")
async def clear_memory(user_id: str):
    """Clear all memory for a specific user"""
    try:
        # Import here to avoid circular imports
        from memory import clear_user_memory
        await asyncio.to_thread(clear_user_memory, user_id, "./chroma/chroma_memory")
        return {"message": f"Memory cleared for user {user_id}"}
    except Exception as e:
        return {"error": f"Failed to clear memory: {str(e)}"}

@app.post("/chat")
async def chat(req: ChatRequest):
    await asyncio.to_thread(save_user_message, req.user_id, req.message, persist_dir="./chroma/chroma_memory")
    mem_docs = await asyncio.to_thread(retrieve_user_memory, req.user_id, req.message, 3, "./chroma/chroma_memory")
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
    return {"response": response}
