# Qudus Portfolio Chatbot

A serverless AI chatbot for Qudus Abolade's portfolio website using Retrieval Augmented Generation (RAG) to answer questions about Qudus's skills, experience, and projects.

## Overview

This repository contains a serverless function that powers the chatbot on Qudus's portfolio website. It uses RAG to retrieve relevant information from various sources and generate accurate responses.

### Serverless Architecture

The serverless function works like this:

1. **User Interaction**: When a user asks a question through the chat interface, the frontend JavaScript sends the query to the Vercel-hosted serverless function.

2. **API Processing**: The serverless function (`api/chat.py`) receives the query, processes it, and forwards it to OpenAI's API with context about Qudus.

3. **Response Handling**: OpenAI generates a response, which the serverless function returns to the frontend.

4. **No Server Management**: No server maintenance needed - Vercel handles scaling, availability, and infrastructure.

### RAG Implementation

The Retrieval Augmented Generation (RAG) system pulls information from:

- Portfolio website
- Resume and other documents in the data directory
- LinkedIn profile
- GitHub profile and repositories

## Setup

### Prerequisites

- Vercel account
- OpenAI API key
- Python 3.9+

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/qudus4l/qudus-portfolio-chat.git
   cd qudus-portfolio-chat
   ```

2. Set up the virtual environment and install dependencies:
   ```bash
   ./setup_venv.sh
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. Add your data:
   - Place your resume and other documents in the `data/` directory
   - Generate LinkedIn profile data: `python scripts/scrape_linkedin.py`

6. Run the ingestion script:
   ```bash
   python scripts/ingest.py
   ```

   Or use the all-in-one update script:
   ```bash
   ./scripts/update_kb.sh
   ```

7. Test locally with Vercel CLI:
   ```bash
   vercel dev
   ```

### Deployment

1. Deploy to Vercel:
   ```bash
   ./scripts/deploy.sh
   ```

   Or manually:
   ```bash
   vercel --prod
   ```

2. Add your OpenAI API key as an environment variable in the Vercel dashboard.

3. Update the CORS headers in `api/chat.py` to match your portfolio domain.

## Usage

Send POST requests to the `/api/chat` endpoint with a JSON body:

```json
{
  "query": "What are Qudus's skills in machine learning?"
}
```

The API will respond with:

```json
{
  "answer": "Qudus has expertise in various machine learning areas including..."
}
```

## Updating Data

To keep your chatbot's knowledge up to date:

1. Run the knowledge base update script:
   ```bash
   ./scripts/update_kb.sh
   ```

   This script will:
   - Generate your LinkedIn profile data
   - Process all documents in the data directory
   - Update the vector store

2. Deploy the updated vector store to Vercel

## Scripts

This repository includes several utility scripts:

1. **`setup_venv.sh`**: Sets up a virtual environment and installs dependencies
2. **`scripts/ingest.py`**: Ingests data from various sources and creates the vector database
3. **`scripts/scrape_linkedin.py`**: Generates LinkedIn profile data and saves to a text file
4. **`scripts/update_kb.sh`**: All-in-one script to update the knowledge base
5. **`scripts/update_cors.py`**: Updates CORS headers in the chat.py file based on environment variables
6. **`scripts/deploy.sh`**: Deployment script for Vercel

## Directory Structure

```
qudus-portfolio-chat/
├── api/
│   └── chat.py           # Serverless function
├── data/
│   ├── *.pdf             # Your resume and other PDF documents
│   ├── *.txt             # Text files including LinkedIn profile
│   └── vector_store/     # Generated vector database
├── scripts/
│   ├── ingest.py         # Data ingestion script
│   ├── scrape_linkedin.py # LinkedIn profile generator
│   ├── update_kb.sh      # Knowledge base update script
│   ├── update_cors.py    # CORS header update script
│   └── deploy.sh         # Deployment script
├── venv/                 # Virtual environment (created by setup_venv.sh)
├── setup_venv.sh         # Virtual environment setup script
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel configuration
└── README.md             # Documentation
```

## Implementation Details

### Data Ingestion

The ingestion script (`scripts/ingest.py`) collects data from multiple sources:

1. **Portfolio Website**: Scrapes content from your portfolio website
2. **Documents**: Processes all PDF and text files in the data directory
3. **GitHub**: Fetches your profile information and repository details
4. **LinkedIn**: Uses a locally generated LinkedIn profile data file

### Vector Database

The ingestion script processes the collected data:

1. **Chunking**: Splits documents into 1000-character chunks with 200-character overlaps
2. **Embedding**: Creates vector embeddings using OpenAI's embedding model
3. **Indexing**: Stores the embeddings in a FAISS vector database for efficient retrieval

### Query Processing

When a user asks a question:

1. **Retrieval**: The system finds the top 5 most relevant chunks from the vector database
2. **Context Building**: The retrieved chunks are combined to create context
3. **Generation**: OpenAI's model generates a response based on the retrieved context
4. **Fallback**: If retrieval fails, a default context is used

## License

MIT 