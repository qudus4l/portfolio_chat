from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import os
import json
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import logging

app = FastAPI()

# Set allowed origins for CORS
PORTFOLIO_DOMAIN = os.environ.get("PORTFOLIO_DOMAIN", "http://qudus4l.tech")
# Support multiple domains and both http/https
allowed_origins = [
    PORTFOLIO_DOMAIN,
    PORTFOLIO_DOMAIN.replace("http://", "https://"),  # Support both protocols
    "http://localhost:3000",  # Local development
    "http://127.0.0.1:3000",  # Local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def retrieve_context(query: str) -> str:
    """
    Retrieve relevant context from the vector database.
    Args:
        query: User's question
    Returns:
        Relevant context as a string
    """
    try:
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.load_local("data/vector_store", embeddings)
        docs = vector_store.similarity_search(query, k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
        return context
    except Exception as e:
        logging.error(f"Error retrieving context: {str(e)}")
        return get_default_context()

def query_openai_with_context(query: str, context: str) -> Dict[str, Any]:
    """
    Send a query to OpenAI API with retrieved context.
    Args:
        query: User's question
        context: Retrieved context from vector database
    Returns:
        OpenAI API response
    """
    import openai
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    openai.api_key = api_key
    system_message = f"""You are a helpful assistant for Qudus Abolade, an ML/AI Engineer. \
    Answer questions about Qudus based on the following information:\n\n{context}\n\nIf the information to answer the question is not in the context provided, use this general information:\n- Qudus is an AI Engineer with expertise in developing production-grade language and vision systems\n- Specializes in Retrieval Augmented Generation (RAG), multilingual NLP, and computer vision\n- Has worked at Curacel, engineering intelligent systems for healthcare, customer service, and insurance automation\n- Technical expertise includes LLMs, computer vision, and full-stack AI development\n- Is a 2024 Nigeria Higher Education Foundation (NHEF) Scholar\n- Has 2+ years of experience in the field\n\nKeep answers concise, professional, and accurate. If you don't know the answer to a question, say you don't have that specific information about Qudus rather than making something up."""
    response = openai.chat.completions.create(
        model='gpt-4.1-mini-2025-04-14',
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ],
        temperature=0.7,
        max_tokens=500
    )
    return {"answer": response.choices[0].message.content}

def get_default_context() -> str:
    """
    Get default context about Qudus.
    Returns:
        Default context as a string
    """
    return (
        "Qudus Abolade is an AI Engineer with expertise in developing production-grade language and vision systems.\n"
        "He specializes in Retrieval Augmented Generation (RAG), multilingual NLP, and computer vision.\n"
        "He has worked at Curacel, engineering intelligent systems for healthcare, customer service, and insurance automation.\n"
        "His technical foundation includes deep expertise in LLMs, computer vision, and full-stack AI development.\n"
        "He is a 2024 Nigeria Higher Education Foundation (NHEF) Scholar.\n"
        "He has 2+ years of experience in the field.\n"
        "His skills include Python, SQL, JavaScript, R, TensorFlow, PyTorch, and more."
    )

@app.get("/")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for Render.
    Returns a simple status message.
    """
    return {"status": "healthy", "message": "Qudus Portfolio Chatbot API is running"}

@app.post("/api/chat")
async def chat(request: Request) -> JSONResponse:
    """
    FastAPI endpoint for the RAG-powered chatbot.
    Accepts a JSON body with a 'query' field and returns an answer.
    """
    try:
        body = await request.json()
        query = body.get('query', '')
        if not query:
            return JSONResponse(status_code=400, content={"error": "Query parameter is required"})
        context_info = retrieve_context(query)
        response = query_openai_with_context(query, context_info)
        return JSONResponse(content=response)
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)}) 