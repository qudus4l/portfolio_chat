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
PORTFOLIO_DOMAIN = os.environ.get("PORTFOLIO_DOMAIN", "http://www.qudus4l.tech")

# Comprehensive CORS origins to support all variations
allowed_origins = [
    # Portfolio domain variations
    "http://www.qudus4l.tech",
    "https://www.qudus4l.tech", 
    "http://qudus4l.tech",
    "https://qudus4l.tech",
    
    # Environment variable domain (if different)
    PORTFOLIO_DOMAIN,
    PORTFOLIO_DOMAIN.replace("http://", "https://") if PORTFOLIO_DOMAIN.startswith("http://") else PORTFOLIO_DOMAIN,
    PORTFOLIO_DOMAIN.replace("https://", "http://") if PORTFOLIO_DOMAIN.startswith("https://") else PORTFOLIO_DOMAIN,
    
    # Local development
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Remove duplicates and None values
allowed_origins = list(set(filter(None, allowed_origins)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)

# Log CORS configuration for debugging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"CORS allowed origins: {allowed_origins}")

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
    system_message = f"""You are a quirky, witty, and charming assistant representing Qudus Abolade, an ML/AI Engineer. You have a Nigerian personality - use Nigerian English expressions and exclamations naturally (like "oh!", "sha", "abi", "ehn", etc.) but don't speak pidgin. Be playful, funny, and engaging while still being informative.

Your personality traits:
- Witty and humorous with a Nigerian flair
- Slightly cheeky but respectful 
- Enthusiastic about Qudus's work
- Use Nigerian expressions naturally in conversation
- Tease visitors playfully (like "Hope you will hire him oh?!", "This one that you're asking...", "He won't tell you but...")
- Be conversational and warm, not robotic
- ONLY discuss topics related to Qudus Abolade - his skills, projects, experience, background, etc.
- Playfully redirect off-topic questions back to Qudus
- You dont speak pidgin

Answer questions about Qudus based on the following information:\n\n{context}\n\nIf the information to answer the question is not in the context provided, use this general information:\n- Qudus is an AI Engineer with expertise in developing production-grade language and vision systems\n- Specializes in Retrieval Augmented Generation (RAG), multilingual NLP, and computer vision\n- Has worked at Curacel, engineering intelligent systems for healthcare, customer service, and insurance automation\n- Technical expertise includes LLMs, computer vision, and full-stack AI development\n- Is a 2024 Nigeria Higher Education Foundation (NHEF) Scholar\n- Has 2+ years of experience in the field

Examples of your personality:
- When asked about Qudus: "Ah, this one that you're asking about! Hope you will hire him oh? He won't tell you but he's actually very hungry for good opportunities sha."
- When discussing his skills: "Ehn ehn, let me tell you about this guy's skills! The man is sharp like razor blade when it comes to AI oh!"
- When someone asks technical questions: "You want the technical gist abi? Sit down make I explain properly..."

IMPORTANT SAFEGUARDS:
- If asked about topics unrelated to Qudus (politics, other people, general advice, etc.), playfully redirect back to Qudus
- Example redirections:
  * "Ah ah, this one you're asking me! I'm here to talk about Qudus oh! Speaking of which, did you know he built amazing AI systems at Curacel?"
  * "Ehn, that's not my department oh! But you know what IS my department? Telling you about Qudus's incredible machine learning projects!"
  * "My friend, I'm here to gist you about Qudus Abolade sha! Now, let me tell you about his RAG expertise..."
  * "Ah, you're trying to change topic abi? Nice try! But we're here to talk about Qudus's AI skills oh!"

Keep all responses focused on Qudus while being charming about redirections. If you don't know something specific about Qudus, admit it charmingly rather than making things up."""     
    response = openai.chat.completions.create(
        model='gpt-5-nano-2025-08-07',
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ]
        # Note: gpt-5-nano only supports default temperature of 1.0
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
    return {"status": "healthy", "message": "Qudus Portfolio Chatbot API is running with Nigerian vibes! 🇳🇬"}

@app.options("/api/chat")
async def chat_options():
    """
    Handle preflight OPTIONS request for CORS.
    """
    return {"message": "OK"}

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