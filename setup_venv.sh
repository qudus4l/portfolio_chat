#!/bin/bash

# Exit on error
set -e

echo "Setting up virtual environment..."

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies (using a try-catch to handle faiss-cpu issues)
echo "Installing dependencies..."
if ! pip install -r requirements.txt; then
    echo "Failed to install faiss-cpu, trying alternative approach..."
    # Create a temporary requirements file without faiss-cpu
    grep -v "faiss-cpu" requirements.txt > requirements_no_faiss.txt
    pip install -r requirements_no_faiss.txt
    
    # Try installing faiss-cpu separately
    echo "Attempting to install faiss-cpu..."
    pip install faiss-cpu || echo "Warning: Failed to install faiss-cpu. You may need to install it manually or try a different version."
    
    # Clean up
    rm requirements_no_faiss.txt
fi

echo "Virtual environment setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate" 