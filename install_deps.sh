#!/bin/zsh
# Quick fix script to install dependencies

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Flask and other dependencies..."
pip install flask==2.2.5
pip install pandas==2.0.3 numpy==1.24.3 matplotlib==3.7.2 seaborn==0.12.2
pip install yfinance==0.2.28 requests==2.31.0 beautifulsoup4==4.12.2
pip install langchain==0.0.300 langchain-community==0.0.10
pip install ollama==0.1.4 plotly==5.15.0 dash==2.9.3

echo "Installation complete. Now you can run the app with:"
echo "python app.py"
