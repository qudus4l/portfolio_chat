from typing import Dict, Any, List
import os
import json
import requests
import glob
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from langchain_community.document_loaders import (
    WebBaseLoader, 
    PDFMinerLoader, 
    TextLoader,
    DirectoryLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


def ingest_data() -> None:
    """
    Ingest data from various sources and create a vector database.
    
    This function collects data from portfolio website, resume PDF,
    GitHub profile and repositories, and LinkedIn profile, then
    creates a vector database for semantic search.
    """
    print("Starting data ingestion...")
    documents = []
    
    # 1. Load portfolio website comprehensively
    print("Loading portfolio website with comprehensive scraping...")
    try:
        from scrape_portfolio import scrape_portfolio_website
        portfolio_docs = scrape_portfolio_website("http://www.qudus4l.tech")
        documents.extend(portfolio_docs)
        print(f"Loaded {len(portfolio_docs)} documents from comprehensive portfolio scraping")
        print("  - Main page sections")
        print("  - All project detail pages") 
        print("  - All work experience detail pages")
    except Exception as e:
        print(f"Error with comprehensive portfolio scraping: {str(e)}")
        print("Falling back to basic web scraping...")
        try:
            portfolio_loader = WebBaseLoader("https://qudus4l.github.io")
            portfolio_docs = portfolio_loader.load()
            documents.extend(portfolio_docs)
            print(f"Loaded {len(portfolio_docs)} documents from basic portfolio scraping")
        except Exception as e2:
            print(f"Error with basic portfolio scraping: {str(e2)}")
    
    # 2. Load all PDF files in data directory
    print("Loading PDF files from data directory...")
    pdf_files = glob.glob("data/*.pdf")
    for pdf_file in pdf_files:
        try:
            pdf_loader = PDFMinerLoader(pdf_file)
            pdf_docs = pdf_loader.load()
            documents.extend(pdf_docs)
            print(f"Loaded {len(pdf_docs)} documents from {pdf_file}")
        except Exception as e:
            print(f"Error loading {pdf_file}: {str(e)}")
    
    # 3. Load all text files in data directory
    print("Loading text files from data directory...")
    txt_files = glob.glob("data/*.txt")
    for txt_file in txt_files:
        try:
            txt_loader = TextLoader(txt_file)
            txt_docs = txt_loader.load()
            documents.extend(txt_docs)
            print(f"Loaded {len(txt_docs)} documents from {txt_file}")
        except Exception as e:
            print(f"Error loading {txt_file}: {str(e)}")
    
    # 4. Scrape GitHub profile and repositories
    print("Scraping GitHub profile...")
    github_username = "qudus4l"
    github_docs = scrape_github(github_username)
    documents.extend(github_docs)
    print(f"Loaded {len(github_docs)} documents from GitHub")
    
    # 5. Scrape LinkedIn profile
    print("Scraping LinkedIn profile...")
    linkedin_url = "https://linkedin.com/in/qudus-abolade"
    linkedin_docs = scrape_linkedin(linkedin_url)
    documents.extend(linkedin_docs)
    print(f"Loaded {len(linkedin_docs)} documents from LinkedIn")
    
    print(f"Total documents collected: {len(documents)}")
    
    # Split documents into chunks
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    
    print(f"Total chunks created: {len(chunks)}")
    
    # Create vector store
    print("Creating vector store...")
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Save vector store for future use
    print("Saving vector store...")
    vector_store.save_local("data/vector_store")
    
    print("Data ingestion complete!")


def scrape_github(username: str) -> List[Document]:
    """
    Scrape GitHub profile and repositories.
    
    Args:
        username: GitHub username
        
    Returns:
        List of documents containing GitHub profile and repository information
    """
    documents = []
    
    # Profile information
    profile_url = f"https://api.github.com/users/{username}"
    repos_url = f"https://api.github.com/users/{username}/repos"
    
    try:
        # Get profile data
        profile_response = requests.get(profile_url)
        profile_data = profile_response.json()
        
        profile_text = f"GitHub Profile: {username}\n"
        profile_text += f"Name: {profile_data.get('name', '')}\n"
        profile_text += f"Bio: {profile_data.get('bio', '')}\n"
        profile_text += f"Location: {profile_data.get('location', '')}\n"
        profile_text += f"Public Repositories: {profile_data.get('public_repos', 0)}\n"
        
        documents.append(Document(page_content=profile_text, metadata={"source": "github_profile"}))
        
        # Get repositories
        repos_response = requests.get(repos_url)
        repos_data = repos_response.json()
        
        for repo in repos_data:
            repo_text = f"Repository: {repo.get('name')}\n"
            repo_text += f"Description: {repo.get('description', '')}\n"
            repo_text += f"Language: {repo.get('language', '')}\n"
            repo_text += f"Stars: {repo.get('stargazers_count', 0)}\n"
            repo_text += f"Forks: {repo.get('forks_count', 0)}\n"
            repo_text += f"URL: {repo.get('html_url', '')}\n"
            
            documents.append(Document(page_content=repo_text, metadata={"source": f"github_repo_{repo.get('name')}"}))
            
            # Get README content if available
            readme_url = f"https://raw.githubusercontent.com/{username}/{repo.get('name')}/main/README.md"
            readme_response = requests.get(readme_url)
            
            if readme_response.status_code == 200:
                readme_text = f"README for {repo.get('name')}:\n{readme_response.text}"
                documents.append(Document(page_content=readme_text, metadata={"source": f"github_readme_{repo.get('name')}"}))
    
    except Exception as e:
        print(f"Error scraping GitHub: {str(e)}")
    
    return documents


def scrape_linkedin(url: str) -> List[Document]:
    """
    Scrape LinkedIn profile data.
    
    Note: Due to LinkedIn's restrictions on scraping, this function attempts to
    scrape the profile but falls back to using a local file if scraping fails.
    
    Args:
        url: LinkedIn profile URL
        
    Returns:
        List of documents containing LinkedIn profile information
    """
    documents = []
    
    try:
        print("Attempting to scrape LinkedIn profile...")
        # Use web parser to get LinkedIn data
        # Note: This is a placeholder. In practice, LinkedIn actively prevents scraping
        # and you would need to use their API or a specialized service
        
        # For now, we'll use the mcp_Zapier_MCP_web_parser_by_zapier_parse_webpage tool
        # if it's available, otherwise we'll fall back to the local file approach
        
        # Since direct scraping is challenging, we'll use the local file approach
        # but keep this function for future enhancement
        
        raise NotImplementedError("LinkedIn scraping is not implemented")
    
    except Exception as e:
        print(f"LinkedIn scraping failed: {str(e)}")
        print("Falling back to local LinkedIn profile data...")
        
        # Check if LinkedIn data file exists
        if os.path.exists("data/linkedin_profile.txt"):
            try:
                linkedin_loader = TextLoader("data/linkedin_profile.txt")
                linkedin_docs = linkedin_loader.load()
                documents.extend(linkedin_docs)
                print(f"Loaded LinkedIn data from local file")
            except Exception as e:
                print(f"Error loading LinkedIn data from file: {str(e)}")
        else:
            # Create a placeholder document with enhanced information
            print("LinkedIn profile data file not found at data/linkedin_profile.txt")
            print("Creating a placeholder LinkedIn document")
            linkedin_text = """
            Qudus Abolade
            ML/AI Engineer
            
            About:
            Passionate ML/AI Engineer with expertise in developing production-grade language and vision systems. 
            Specializing in Retrieval Augmented Generation (RAG), multilingual NLP, and computer vision. 
            Committed to creating AI solutions that solve real-world problems.
            
            Experience:
            - AI Engineer at Curacel (2024 - Present)
              Developing intelligent systems for healthcare, customer service, and insurance automation
              - Built end-to-end RAG systems for document processing and information retrieval
              - Implemented computer vision solutions for automated claims processing
              - Developed multilingual NLP models for customer support
            
            Education:
            - Nigeria Higher Education Foundation (NHEF) Scholar, 2024
            - B.Sc. Computer Science, University of Lagos
            
            Skills:
            - Machine Learning & Deep Learning
            - Natural Language Processing
            - Computer Vision
            - Retrieval Augmented Generation (RAG)
            - Python, SQL, JavaScript, R
            - TensorFlow, PyTorch, Hugging Face
            - LangChain, LlamaIndex
            - Docker, Kubernetes
            - AWS, GCP, Azure
            
            Projects:
            - Developed a multilingual RAG system for document processing in multiple languages
            - Created a computer vision system for automated medical image analysis
            - Built a conversational AI assistant for customer service automation
            - Implemented a recommendation system for personalized content delivery
            """
            
            documents.append(Document(page_content=linkedin_text, metadata={"source": "linkedin_profile"}))
    
    return documents


if __name__ == "__main__":
    ingest_data() 