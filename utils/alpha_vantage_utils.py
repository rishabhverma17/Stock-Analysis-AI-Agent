"""
Alpha Vantage API utility functions for the Chain of Agents stock analysis system
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, Any, List, Optional

from config import ALPHA_VANTAGE_API_KEY, ALPHA_VANTAGE_BASE_URL
from utils.stock_utils import save_to_cache, get_from_cache

def fetch_alpha_vantage_time_series(symbol: str, period: str) -> Dict[str, Any]:
    """
    Fetch time series data from Alpha Vantage API
    
    Args:
        symbol: Stock symbol
        period: Time period (1w, 1mo, 6mo, 1y, etc.)
        
    Returns:
        Dictionary with historical price data
    """
    # Check cache first
    cached_data = get_from_cache(symbol, period, data_type='alpha_vantage_ts')
    if cached_data is not None:
        print(f"Using cached Alpha Vantage time series data for {symbol}")
        return cached_data
    
    # For testing purposes, force 1y period which is more reliable
    print(f"Original period requested: {period}")
    print(f"Using 1y period for more reliable data")
    reliable_period = "1y"
    
    # Map our periods to Alpha Vantage functions and outputsize
    function = "TIME_SERIES_DAILY"  # Default
    outputsize = "compact"  # Default: last 100 data points
    
    # For longer periods, use full data
    if reliable_period in ['6mo', '1y', '3y', '5y', '10y', 'max']:
        outputsize = "full"
    
    # For intraday data (typically for 1w)
    # NOTE: Disabled intraday to fix issues with data retrieval
    # Always use daily data regardless of period for more reliability
    use_intraday = False  # Set to False to disable intraday
    if reliable_period == '1w' and use_intraday:
        function = "TIME_SERIES_INTRADAY"
        interval = "60min"  # Use hourly data for 1 week
    
    # Prepare API request parameters
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "outputsize": outputsize,
    }
    
    # Add interval for intraday data
    if function == "TIME_SERIES_INTRADAY":
        params["interval"] = interval
    
    try:
        # Make API request
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Debug output to see the raw API response
        print(f"Alpha Vantage API response for {symbol} with function {function}:")
        print(f"Response keys: {list(data.keys())}")
        
        # Check for error message in response
        if "Error Message" in data:
            print(f"Alpha Vantage API error: {data['Error Message']}")
            return {"success": False, "error": data["Error Message"]}
        
        # Parse response based on the function
        if function == "TIME_SERIES_INTRADAY":
            time_series_key = f"Time Series ({interval})"
        else:
            time_series_key = "Time Series (Daily)"
        
        if time_series_key not in data:
            print(f"Missing expected key '{time_series_key}' in response. Available keys: {list(data.keys())}")
            return {"success": False, "error": f"Unexpected API response format, missing {time_series_key}"}
        
        # Extract time series data
        time_series = data[time_series_key]
        print(f"Found {len(time_series)} data points in time series")
        
        # Convert to list of records
        historical_data = []
        for date, values in time_series.items():
            historical_data.append({
                "Date": date,
                "Open": float(values["1. open"]),
                "High": float(values["2. high"]),
                "Low": float(values["3. low"]),
                "Close": float(values["4. close"]),
                "Volume": int(values["5. volume"])
            })
        
        # Sort by date (most recent first)
        historical_data.sort(key=lambda x: x["Date"], reverse=True)
        
        # Filter based on period
        if period == '1w':
            days = 7
        elif period == '1mo':
            days = 30
        elif period == '6mo':
            days = 180
        elif period == '1y':
            days = 365
        elif period == '3y':
            days = 365 * 3
        elif period == '5y':
            days = 365 * 5
        else:  # 10y or max
            days = 365 * 10
        
        # Convert to ISO format dates
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered_data = [item for item in historical_data if item["Date"] >= cutoff_date]
        
        # Get company information
        company_info = fetch_alpha_vantage_company_overview(symbol)
        
        result = {
            "success": True,
            "data": filtered_data,
            "info": company_info.get("info", {
                "symbol": symbol,
                "shortName": symbol,
                "longName": symbol,
                "dataSource": "Alpha Vantage"
            }),
            "period": period,
            "timestamp": datetime.now().isoformat(),
            "source": "alpha_vantage"
        }
        
        # Save to cache
        save_to_cache(result, symbol, period, data_type='alpha_vantage_ts')
        
        return result
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error processing data: {str(e)}"}

def fetch_alpha_vantage_company_overview(symbol: str) -> Dict[str, Any]:
    """
    Fetch company overview data from Alpha Vantage API
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dictionary with company information
    """
    # Check cache first
    cached_data = get_from_cache(symbol, "overview", data_type='alpha_vantage_overview')
    if cached_data is not None:
        print(f"Using cached Alpha Vantage company overview for {symbol}")
        return cached_data
    
    # Prepare API request parameters
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    
    try:
        # Make API request
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check for error message or empty response
        if "Error Message" in data or not data:
            return {"success": False, "error": data.get("Error Message", "Empty response")}
        
        # Map Alpha Vantage fields to our standard format
        info = {
            "symbol": data.get("Symbol", symbol),
            "shortName": data.get("Name", symbol),
            "longName": data.get("Name", symbol),
            "sector": data.get("Sector", ""),
            "industry": data.get("Industry", ""),
            "website": data.get("Address", ""),
            "marketCap": float(data.get("MarketCapitalization", 0)) if data.get("MarketCapitalization") else None,
            "trailingPE": float(data.get("TrailingPE", 0)) if data.get("TrailingPE") else None,
            "dividendYield": float(data.get("DividendYield", 0)) if data.get("DividendYield") else None,
            "fiftyTwoWeekHigh": float(data.get("52WeekHigh", 0)) if data.get("52WeekHigh") else None,
            "fiftyTwoWeekLow": float(data.get("52WeekLow", 0)) if data.get("52WeekLow") else None,
            "description": data.get("Description", ""),
            "exchange": data.get("Exchange", ""),
            "currency": data.get("Currency", "USD"),
            "country": data.get("Country", ""),
            "dataSource": "Alpha Vantage"
        }
        
        result = {
            "success": True,
            "info": info,
            "timestamp": datetime.now().isoformat(),
            "source": "alpha_vantage"
        }
        
        # Save to cache
        save_to_cache(result, symbol, "overview", data_type='alpha_vantage_overview')
        
        return result
    
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error processing data: {str(e)}"}

def fetch_alpha_vantage_news(symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch news for a stock symbol from Alpha Vantage API
    
    Args:
        symbol: Stock symbol
        limit: Maximum number of news items to return
        
    Returns:
        List of news items
    """
    # Check cache first (with a shorter expiry time for news)
    cached_data = get_from_cache(symbol, "news", data_type='alpha_vantage_news', max_age_hours=6)
    if cached_data is not None:
        print(f"Using cached Alpha Vantage news for {symbol}")
        return cached_data
    
    # Prepare API request parameters
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "limit": min(limit * 3, 50)  # Request more than we need to filter for relevance
    }
    
    try:
        # Make API request
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check for error message or missing feed
        if "Error Message" in data or "feed" not in data:
            print(f"Alpha Vantage news API error: {data.get('Error Message', 'No feed data')}")
            return []
        
        # Extract news items
        all_news = data.get("feed", [])
        
        # Filter for most relevant news (matching our symbol exactly)
        relevant_news = []
        for item in all_news:
            ticker_sentiments = item.get("ticker_sentiment", [])
            for ticker in ticker_sentiments:
                if ticker.get("ticker") == symbol:
                    relevance = float(ticker.get("relevance_score", 0))
                    # Only include highly relevant news
                    if relevance > 0.5:
                        relevant_news.append({
                            "relevance": relevance,
                            "news_item": item
                        })
        
        # Sort by relevance and limit
        relevant_news.sort(key=lambda x: x["relevance"], reverse=True)
        top_news = relevant_news[:limit]
        
        # Format news items
        formatted_news = []
        for item in top_news:
            news = item["news_item"]
            formatted_news.append({
                "title": news.get("title", ""),
                "publisher": news.get("source", ""),
                "link": news.get("url", ""),
                "published": news.get("time_published", ""),
                "summary": news.get("summary", ""),
                "sentiment": news.get("overall_sentiment_label", "")
            })
        
        # Save to cache
        save_to_cache(formatted_news, symbol, "news", data_type='alpha_vantage_news')
        
        return formatted_news
    
    except requests.exceptions.RequestException as e:
        print(f"Alpha Vantage news API request failed: {str(e)}")
        return []
    except Exception as e:
        print(f"Error processing Alpha Vantage news: {str(e)}")
        return []

def fetch_alpha_vantage_fundamentals(symbol: str) -> Dict[str, Any]:
    """
    Fetch fundamental data for a stock from Alpha Vantage API
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dictionary with fundamental data
    """
    # Check cache first
    cached_data = get_from_cache(symbol, "fundamentals", data_type='alpha_vantage_fundamentals')
    if cached_data is not None:
        print(f"Using cached Alpha Vantage fundamentals for {symbol}")
        return cached_data
    
    fundamentals = {}
    
    # Get income statement
    income_statement = _fetch_alpha_vantage_income_statement(symbol)
    if income_statement:
        fundamentals["income_statement"] = income_statement
    
    # Get balance sheet
    balance_sheet = _fetch_alpha_vantage_balance_sheet(symbol)
    if balance_sheet:
        fundamentals["balance_sheet"] = balance_sheet
    
    # Get cash flow
    cash_flow = _fetch_alpha_vantage_cash_flow(symbol)
    if cash_flow:
        fundamentals["cash_flow"] = cash_flow
    
    # Get earnings
    earnings = _fetch_alpha_vantage_earnings(symbol)
    if earnings:
        fundamentals["earnings"] = earnings
    
    # Save to cache if we have any data
    if fundamentals:
        save_to_cache(fundamentals, symbol, "fundamentals", data_type='alpha_vantage_fundamentals')
    
    return fundamentals

def _fetch_alpha_vantage_income_statement(symbol: str) -> Dict[str, Any]:
    """Helper function to fetch income statement"""
    params = {
        "function": "INCOME_STATEMENT",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "Error Message" in data or "annualReports" not in data:
            return {}
        
        return {
            "annual": data.get("annualReports", []),
            "quarterly": data.get("quarterlyReports", [])
        }
    except Exception as e:
        print(f"Error fetching income statement: {str(e)}")
        return {}

def _fetch_alpha_vantage_balance_sheet(symbol: str) -> Dict[str, Any]:
    """Helper function to fetch balance sheet"""
    params = {
        "function": "BALANCE_SHEET",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "Error Message" in data or "annualReports" not in data:
            return {}
        
        return {
            "annual": data.get("annualReports", []),
            "quarterly": data.get("quarterlyReports", [])
        }
    except Exception as e:
        print(f"Error fetching balance sheet: {str(e)}")
        return {}

def _fetch_alpha_vantage_cash_flow(symbol: str) -> Dict[str, Any]:
    """Helper function to fetch cash flow"""
    params = {
        "function": "CASH_FLOW",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "Error Message" in data or "annualReports" not in data:
            return {}
        
        return {
            "annual": data.get("annualReports", []),
            "quarterly": data.get("quarterlyReports", [])
        }
    except Exception as e:
        print(f"Error fetching cash flow: {str(e)}")
        return {}

def _fetch_alpha_vantage_earnings(symbol: str) -> Dict[str, Any]:
    """Helper function to fetch earnings"""
    params = {
        "function": "EARNINGS",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    
    try:
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "Error Message" in data or "annualEarnings" not in data:
            return {}
        
        return {
            "annual": data.get("annualEarnings", []),
            "quarterly": data.get("quarterlyEarnings", [])
        }
    except Exception as e:
        print(f"Error fetching earnings: {str(e)}")
        return {}
