#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # Exit on error

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

# Run data ingestion to create vector store
echo "Running data ingestion..."
python scripts/ingest.py

echo "Build completed successfully!"
