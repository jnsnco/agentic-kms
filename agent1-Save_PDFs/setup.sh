#!/bin/bash
# Setup script for URL to PDF Agent

echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y wkhtmltopdf chromium-browser python3-pip

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo "Making agent script executable..."
chmod +x url_to_pdf_agent.py

echo "Setup complete! You can now run the agent with:"
echo "python3 url_to_pdf_agent.py <input_file_or_directory>"