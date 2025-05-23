#!/bin/bash

# Exit on error
set -e

echo "Starting knowledge base update process..."

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run setup_venv.sh first."
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Try to scrape LinkedIn profile
echo "Attempting to scrape LinkedIn profile data..."
python scripts/scrape_linkedin.py --url "https://linkedin.com/in/qudus-abolade" --output "data/linkedin_profile.txt"

# Run data ingestion
echo "Running data ingestion process..."
python scripts/ingest.py

echo "Knowledge base update complete!"
echo "The vector store has been created/updated in data/vector_store/"

# Deactivate virtual environment
deactivate 