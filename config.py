"""
Configuration settings for the Chain of Agents stock analysis system
"""

# Ollama model configuration
OLLAMA_MODEL = "deepseek-r1:8b"  # Using the model you have available
OLLAMA_HOST = "http://127.0.0.1:11434"  # Using IP address instead of localhost to avoid TLS issues
OLLAMA_API_ENDPOINT = "/api/chat"  # Using chat endpoint

# Alpha Vantage API configuration
ALPHA_VANTAGE_API_KEY = "2V8STMMT7XUWMCVS"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# Agent settings
AGENT_1_NAME = "DataCollectorAgent"
AGENT_2_NAME = "AnalysisAgent"
AGENT_3_NAME = "VisualizationAgent"

# Time periods for historical data
TIME_PERIODS = {
    "1w": "1 Week",
    "1mo": "1 Month",
    "6mo": "6 Months",
    "1y": "1 Year",
    "3y": "3 Years",
    "5y": "5 Years",
    "10y": "10 Years",
    "max": "All Time"
}

# Flask app configuration
PORT = 5001
DEBUG = True

# Data storage
DATA_DIR = "data"
