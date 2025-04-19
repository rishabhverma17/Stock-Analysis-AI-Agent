#!/bin/zsh
# Setup script for ChainOfAgents project

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python -m venv venv
  if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment. Make sure Python is installed."
    exit 1
  fi
  echo "Virtual environment created successfully."
else
  echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install setuptools first
echo "Upgrading pip and installing setuptools..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
  echo "Warning: Ollama is not installed or not in PATH."
  echo "Please install Ollama from: https://ollama.ai/download"
fi

# Check if Deepseek model is available
if command -v ollama &> /dev/null; then
  if ! ollama list | grep -q "deepseek-coder:1.5b"; then
    echo "Deepseek model not found. Would you like to download it now? (y/n)"
    read download_model
    if [[ $download_model == "y" || $download_model == "Y" ]]; then
      echo "Downloading Deepseek model..."
      ollama pull deepseek-coder:1.5b
    else
      echo "Please download the model manually with: ollama pull deepseek-coder:1.5b"
    fi
  else
    echo "Deepseek model is already available."
  fi
fi

echo ""
echo "Setup complete! To run the project:"
echo "1. Make sure Ollama is running"
echo "2. Activate the environment with: source venv/bin/activate"
echo "3. Start the application with: python app.py"
echo ""
echo "Access the web interface at: http://localhost:5000"
