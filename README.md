# Chain of Agents Stock Analysis System

A modern stock analysis application powered by a chain of AI agents to collect data, perform analysis, and create visualizations.

![Chain of Agents](https://i.imgur.com/JZT6bL5.png)

## Overview

This application uses a pipeline of specialized agents to analyze stocks:

1. **Data Collector Agent**: Fetches historical stock data, news, and fundamentals from Alpha Vantage
2. **Analysis Agent**: Examines the data and generates insights and recommendations
3. **Visualization Agent**: Creates interactive charts and visual representations of the analysis

## Features

- Modern, responsive UI with sleek animations and visual feedback
- Real-time agent status visualization to show pipeline progress
- Interactive stock charts with price history and technical indicators
- Comprehensive analysis with buy/sell/hold recommendations
- Support for various time periods (1 week to 10 years)

## Requirements

- Python 3.10+
- Alpha Vantage API key (free tier is sufficient)
- Ollama with deepseek-coder model (for LLM capabilities)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ChainOfAgents.git
   cd ChainOfAgents
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Configure your API keys in `config.py`:
   ```python
   # Alpha Vantage API key
   ALPHA_VANTAGE_API_KEY = "your_api_key_here"
   ```

## Running the Application

1. Ensure your virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```

2. Start the Flask application:
   ```bash
   python app.py
   ```

3. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

4. Enter a stock symbol (e.g., AAPL, MSFT, GOOG) and select a time period to analyze

5. To stop the application, press `Ctrl+C` in the terminal

6. When finished, deactivate the virtual environment:
   ```bash
   deactivate
   ```

## Architecture

### Agent Pipeline

The application uses a chain of agents, each with a specialized role:

1. **Data Collector Agent**: 
   - Fetches stock data from Alpha Vantage
   - Retrieves news articles and fundamental data
   - Caches responses to minimize API calls

2. **Analysis Agent**:
   - Processes historical price data
   - Analyzes trends and patterns
   - Generates buy/sell/hold recommendations with confidence levels

3. **Visualization Agent**:
   - Creates interactive price charts
   - Visualizes key technical indicators
   - Provides visual insights to support the analysis

### Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Backend**: Flask, Python
- **Data Visualization**: Plotly.js
- **API Integration**: Alpha Vantage, Yahoo Finance (fallback)
- **LLM Integration**: Ollama with deepseek-coder model

## Troubleshooting

- **Empty Charts**: If charts appear empty, check your Alpha Vantage API key in `config.py`
- **Slow Responses**: The free tier of Alpha Vantage has rate limits; cached responses are used when available
- **SSL/TLS Errors**: These are handled by the application and can be safely ignored

## License

MIT
