#!/usr/bin/env python3
from typing import Dict, Any, List
import os
import re

def update_cors_headers() -> None:
    """
    Update CORS headers in the chat.py file based on environment variable.
    
    This function reads the PORTFOLIO_DOMAIN environment variable and updates
    the CORS headers in the chat.py file to match.
    """
    portfolio_domain = os.environ.get('PORTFOLIO_DOMAIN', '*')
    
    # Path to the chat.py file
    chat_file_path = os.path.join('api', 'chat.py')
    
    if not os.path.exists(chat_file_path):
        print(f"Error: {chat_file_path} not found")
        return
    
    # Read the file content
    with open(chat_file_path, 'r') as file:
        content = file.read()
    
    # Replace the CORS origin
    pattern = r"'Access-Control-Allow-Origin': '([^']*)'"
    replacement = f"'Access-Control-Allow-Origin': '{portfolio_domain}'"
    
    updated_content = re.sub(pattern, replacement, content)
    
    # Write the updated content back to the file
    with open(chat_file_path, 'w') as file:
        file.write(updated_content)
    
    print(f"Updated CORS headers to allow origin: {portfolio_domain}")


if __name__ == "__main__":
    update_cors_headers() 