#!/bin/bash

# Exit on error
set -e

echo "Starting deployment process..."

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run setup_venv.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create one based on env.example."
    exit 1
fi

# Load environment variables
source .env

# Update CORS headers
echo "Updating CORS headers..."
python scripts/update_cors.py

# Run data ingestion if vector store doesn't exist
if [ ! -d "data/vector_store" ]; then
    echo "Vector store not found. Running data ingestion..."
    python scripts/ingest.py
else
    echo "Vector store found. Skipping data ingestion."
    echo "To force re-ingestion, delete the data/vector_store directory."
fi

# Deactivate virtual environment before deploying to Vercel
deactivate

# Deploy to Vercel
echo "Deploying to Vercel..."
vercel --prod

echo "Deployment complete!" 