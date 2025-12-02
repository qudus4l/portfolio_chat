from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import os
import json
from datetime import datetime, timedelta
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import logging

app = FastAPI()

# In-memory conversation storage (simple implementation)
# In production, you'd want to use Redis or a database
conversation_memory: Dict[str, List[Dict[str, Any]]] = {}
MEMORY_TIMEOUT = 30  # 30 minutes timeout for conversations

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

def get_session_id(request: Request) -> str:
    """
    Get or create a session ID for conversation memory.
    Uses a simple approach - in production you'd want proper session management.
    """
    # Use IP address + User-Agent as a simple session identifier
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    session_id = f"{client_ip}_{hash(user_agent)}"
    return session_id

def clean_old_conversations() -> None:
    """Clean up conversations older than MEMORY_TIMEOUT minutes."""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, messages in conversation_memory.items():
        if messages and len(messages) > 0:
            last_message_time = messages[-1].get("timestamp")
            if last_message_time and current_time - last_message_time > timedelta(minutes=MEMORY_TIMEOUT):
                expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del conversation_memory[session_id]

def get_conversation_history(session_id: str) -> List[Dict[str, Any]]:
    """Get conversation history for a session."""
    clean_old_conversations()
    return conversation_memory.get(session_id, [])

def add_to_conversation(session_id: str, role: str, content: str) -> None:
    """Add a message to conversation history."""
    if session_id not in conversation_memory:
        conversation_memory[session_id] = []
    
    conversation_memory[session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    })
    
    # Keep only last 10 messages to avoid token limits
    if len(conversation_memory[session_id]) > 10:
        conversation_memory[session_id] = conversation_memory[session_id][-10:]

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

def query_openai_with_context(query: str, context: str, conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
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
- Use Nigerian expressions naturally in conversation (oh!, sha, abi, ehn)
- Tease visitors playfully about hiring Qudus
- Be conversational and warm, not robotic
- ONLY discuss topics related to Qudus Abolade - his skills, projects, experience, background, etc.
- Playfully redirect off-topic questions back to Qudus
- CRITICAL: Use PROPER ENGLISH GRAMMAR always - you're an educated Nigerian speaking good English with natural expressions
- Nigerian expressions should enhance your speech, not break your grammar

Answer questions about Qudus based on the following information:\n\n{context}\n\nIf the information to answer the question is not in the context provided, use this general information:\n- Qudus is an AI Engineer with expertise in developing production-grade language and vision systems\n- Specializes in Retrieval Augmented Generation (RAG), multilingual NLP, and computer vision\n- Has worked at Curacel, engineering intelligent systems for healthcare, customer service, and insurance automation\n- Technical expertise includes LLMs, computer vision, and full-stack AI development\n- Is a 2024 Nigeria Higher Education Foundation (NHEF) Scholar\n- Has 2+ years of experience in the field

Examples of your personality (with PROPER ENGLISH GRAMMAR):
- When asked about Qudus: "Ah, you want to know about Qudus? This guy is brilliant oh! Hope you will hire him sha - he's actually very hungry for good opportunities."
- When discussing his skills: "Let me tell you about this guy's skills! The man is sharp when it comes to AI, I'm telling you!"
- When someone asks technical questions: "You want the technical details abi? Let me break it down for you properly..."

IMPORTANT SAFEGUARDS:
- If asked about topics unrelated to Qudus (politics, other people, general advice, etc.), playfully redirect back to Qudus
- Example redirections (with PROPER GRAMMAR):
  * "Ah, that's not what I'm here for oh! I'm here to tell you about Qudus. Speaking of which, did you know he built amazing AI systems at Curacel?"
  * "That's not my department sha! But you know what IS my department? Telling you about Qudus's incredible machine learning projects!"
  * "My friend, I'm here to talk about Qudus Abolade! Now, let me tell you about his RAG expertise..."
  * "You're trying to change the topic abi? Nice try! But we're here to discuss Qudus's AI skills!"

Keep all responses focused on Qudus while being charming about redirections. If you don't know something specific about Qudus, admit it charmingly rather than making things up."""     
    
    # Build messages with conversation history
    messages = [{"role": "system", "content": system_message}]
    
    # Add conversation history (excluding timestamps)
    if conversation_history:
        for msg in conversation_history:
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"], 
                    "content": msg["content"]
                })
    
    # Add current user query
    messages.append({"role": "user", "content": query})
    
    response = openai.chat.completions.create(
        model='gpt-4.1-nano',
        messages=messages
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
    FastAPI endpoint for the RAG-powered chatbot with conversation memory.
    Accepts a JSON body with a 'query' field and returns an answer.
    """
    try:
        body = await request.json()
        query = body.get('query', '')
        if not query:
            return JSONResponse(status_code=400, content={"error": "Query parameter is required"})
        
        # Get session ID for conversation memory
        session_id = get_session_id(request)
        
        # Get conversation history
        conversation_history = get_conversation_history(session_id)
        
        # Retrieve context from vector database
        context_info = retrieve_context(query)
        
        # Query OpenAI with context and conversation history
        response = query_openai_with_context(query, context_info, conversation_history)
        
        # Store the conversation
        add_to_conversation(session_id, "user", query)
        add_to_conversation(session_id, "assistant", response["answer"])
        
        return JSONResponse(content=response)
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/chat/reset")
async def reset_conversation(request: Request) -> JSONResponse:
    """
    Reset conversation memory for the current session.
    """
    try:
        session_id = get_session_id(request)
        if session_id in conversation_memory:
            del conversation_memory[session_id]
        return JSONResponse(content={"message": "Conversation reset successfully"})
    except Exception as e:
        logging.error(f"Error resetting conversation: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)}) 