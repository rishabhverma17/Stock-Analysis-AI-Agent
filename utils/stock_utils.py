"""
Utility functions for the Chain of Agents stock analysis system
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import time
import random
from config import DATA_DIR
from utils.fallback_sources import fetch_marketwatch_data, fetch_fmp_data, generate_basic_price_history

def ensure_data_directory():
    """Ensure the data directory exists"""
    os.makedirs(DATA_DIR, exist_ok=True)
    # Create cache directory
    cache_dir = os.path.join(DATA_DIR, 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir
    
def save_data(data, filename):
    """Save data to a JSON file"""
    ensure_data_directory()
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f)
    return filepath

def load_data(filename):
    """Load data from a JSON file"""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        return json.load(f)
        
def save_to_cache(data, symbol, period, data_type='stock'):
    """Save data to cache with timestamp"""
    cache_dir = ensure_data_directory()
    cache_file = f"{symbol}_{period}_{data_type}.json"
    cache_path = os.path.join(cache_dir, cache_file)
    
    cache_data = {
        'data': data,
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'period': period,
        'type': data_type
    }
    
    with open(cache_path, 'w') as f:
        json.dump(cache_data, f)
    
    return cache_path

def get_from_cache(symbol, period, data_type='stock', max_age_hours=24):
    """Get data from cache if it exists and is not too old"""
    cache_dir = os.path.join(DATA_DIR, 'cache')
    cache_file = f"{symbol}_{period}_{data_type}.json"
    cache_path = os.path.join(cache_dir, cache_file)
    
    if not os.path.exists(cache_path):
        return None
    
    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        # Check if cache is still valid
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        max_age = timedelta(hours=max_age_hours)
        
        if datetime.now() - cache_time > max_age:
            print(f"Cache for {symbol} is too old ({cache_time.isoformat()})")
            return None
        
        print(f"Using cached data for {symbol} from {cache_time.isoformat()}")
        return cache_data['data']
    except Exception as e:
        print(f"Error reading cache for {symbol}: {e}")
        return None

def fetch_stock_data(symbol, period='1y', max_retries=3, use_cache=True):
    """Fetch historical stock data using Alpha Vantage as primary source with fallbacks"""
    
    # Check cache first if enabled
    if use_cache:
        cached_data = get_from_cache(symbol, period)
        if cached_data is not None:
            print(f"Using cached data for {symbol}")
            return cached_data
    
    # Use Alpha Vantage as primary source
    print(f"Fetching data for {symbol} from Alpha Vantage...")
    
    # Import here to avoid circular imports
    from utils.alpha_vantage_utils import fetch_alpha_vantage_time_series
    
    alpha_vantage_data = fetch_alpha_vantage_time_series(symbol, period)
    
    # Debug logging
    print(f"Alpha Vantage response for {symbol}:")
    if alpha_vantage_data.get('success'):
        print(f"  Success: True")
        print(f"  Data points: {len(alpha_vantage_data.get('data', []))}")
        print(f"  Company info: {json.dumps(alpha_vantage_data.get('info', {}), indent=2)[:200]}...")
    else:
        print(f"  Success: False")
        print(f"  Error: {alpha_vantage_data.get('error', 'Unknown error')}")
    
    if alpha_vantage_data['success']:
        if use_cache:
            save_to_cache(alpha_vantage_data, symbol, period)
        return alpha_vantage_data
    
    # If Alpha Vantage failed, try Yahoo Finance as fallback
    print(f"Alpha Vantage data fetch failed for {symbol}, trying Yahoo Finance as fallback...")
    
    yahoo_data = _fetch_from_yahoo(symbol, period, max_retries)
    
    # Debug logging
    print(f"Yahoo Finance response for {symbol}:")
    if yahoo_data.get('success'):
        print(f"  Success: True")
        print(f"  Data points: {len(yahoo_data.get('data', []))}")
        print(f"  Company info: {json.dumps(yahoo_data.get('info', {}), indent=2)[:200]}...")
    else:
        print(f"  Success: False")
        print(f"  Error: {yahoo_data.get('error', 'Unknown error')}")
    
    # If Yahoo Finance succeeded, save to cache and return
    if yahoo_data['success']:
        if use_cache:
            save_to_cache(yahoo_data, symbol, period)
        return yahoo_data
    
    # Try MarketWatch as fallback for company info
    market_watch_data = fetch_marketwatch_data(symbol)
    
    # Try Financial Modeling Prep as another fallback
    fmp_data = fetch_fmp_data(symbol)
    
    # Determine which fallback has better data
    fallback_info = None
    if market_watch_data['success']:
        fallback_info = market_watch_data['info']
    elif fmp_data['success']:
        fallback_info = fmp_data['info']
    else:
        # If all sources failed, create minimal info
        fallback_info = {
            'symbol': symbol,
            'shortName': symbol,
            'longName': symbol,
            'dataSource': 'Fallback Minimal Data'
        }
    
    # Generate synthetic historical data based on current price if available
    current_price = fallback_info.get('currentPrice')
    if current_price is None:
        current_price = 100.0  # Default if we couldn't get a real price
    
    # Determine number of data points based on period
    days = 30  # Default for 1 month
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
    elif period == '10y':
        days = 365 * 10
    
    # Generate synthetic price history
    synthetic_history = generate_basic_price_history(
        base_price=current_price, 
        days=min(days, 365)  # Limit to 1 year for performance
    )
    
    # Create fallback data response
    fallback_response = {
        'success': True,
        'data': synthetic_history,
        'info': fallback_info,
        'period': period,
        'timestamp': datetime.now().isoformat(),
        'source': 'fallback',
        'note': 'This data is from fallback sources due to Yahoo Finance rate limiting'
    }
    
    # Save to cache if enabled
    if use_cache:
        save_to_cache(fallback_response, symbol, period)
    
    return fallback_response

def _fetch_from_yahoo(symbol, period='1y', max_retries=3):
    """Original Yahoo Finance fetching logic"""
    retries = 0
    
    while retries < max_retries:
        try:
            # Add delay to avoid hitting rate limits
            if retries > 0:
                delay = 2 + random.random() * 3  # Random delay between 2-5 seconds
                time.sleep(delay)
            
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            
            # Reset index to make date a column and convert to ISO format string
            hist = hist.reset_index()
            # Check if Date is already a string or convert it to string format
            if pd.api.types.is_datetime64_any_dtype(hist['Date']):
                hist['Date'] = hist['Date'].dt.strftime('%Y-%m-%d')
            else:
                # If it's not a datetime, convert it to string directly
                hist['Date'] = hist['Date'].astype(str)
            
            # Convert to dictionary format
            data_dict = hist.to_dict(orient='records')
            
            # Get additional info - using a separate try/except to handle info errors
            try:
                info = stock.info
                relevant_info = {
                    'symbol': symbol,
                    'shortName': info.get('shortName', symbol),
                    'longName': info.get('longName', ''),
                    'sector': info.get('sector', ''),
                    'industry': info.get('industry', ''),
                    'website': info.get('website', ''),
                    'marketCap': info.get('marketCap', None),
                    'trailingPE': info.get('trailingPE', None),
                    'dividendYield': info.get('dividendYield', None),
                    'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', None),
                    'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', None),
                    'dataSource': 'Yahoo Finance'
                }
            except Exception as info_error:
                print(f"Warning: Could not fetch complete info for {symbol}: {info_error}")
                relevant_info = {
                    'symbol': symbol,
                    'shortName': symbol,
                    'longName': symbol,
                    'dataSource': 'Yahoo Finance (Partial)'
                }
            
            return {
                'success': True,
                'data': data_dict,
                'info': relevant_info,
                'period': period,
                'timestamp': datetime.now().isoformat(),
                'source': 'yahoo'
            }
        except Exception as e:
            retries += 1
            error_msg = str(e)
            print(f"Error fetching data for {symbol} (attempt {retries}/{max_retries}): {error_msg}")
            if retries >= max_retries:
                return {
                    'success': False,
                    'error': f"Failed after {max_retries} attempts: {error_msg}",
                    'period': period,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'yahoo'
                }
            # Add exponential backoff
            time.sleep(retries * 2)

def fetch_news(symbol, limit=5, max_retries=3):
    """Fetch recent news for a stock symbol using Alpha Vantage as primary source"""
    # Import Alpha Vantage utils
    from utils.alpha_vantage_utils import fetch_alpha_vantage_news
    
    print(f"Fetching news for {symbol} from Alpha Vantage...")
    alpha_vantage_news = fetch_alpha_vantage_news(symbol, limit)
    
    # Debug logging
    print(f"Alpha Vantage news response for {symbol}:")
    print(f"  News items: {len(alpha_vantage_news)}")
    if alpha_vantage_news:
        print(f"  First news title: {alpha_vantage_news[0].get('title', 'No title')}")
    
    # If we got news from Alpha Vantage, return it
    if alpha_vantage_news:
        return alpha_vantage_news
    
    # Fallback to Yahoo Finance
    print(f"No news from Alpha Vantage for {symbol}, trying Yahoo Finance as fallback...")
    retries = 0
    
    while retries < max_retries:
        try:
            # Add delay to avoid hitting rate limits
            if retries > 0:
                delay = 2 + random.random() * 3  # Random delay between 2-5 seconds
                time.sleep(delay)
                
            stock = yf.Ticker(symbol)
            
            # Safely access news with additional error handling
            try:
                news = stock.news
                
                # Check if news is a valid list or dictionary to parse
                if not news or not isinstance(news, (list, dict)):
                    print(f"No valid news data available from Yahoo Finance for {symbol}")
                    return []
                    
                # Limit the number of news articles
                news = news[:limit]
                
                # Extract relevant info
                processed_news = []
                for item in news:
                    if not isinstance(item, dict):
                        continue  # Skip non-dictionary items
                        
                    processed_news.append({
                        'title': item.get('title', ''),
                        'publisher': item.get('publisher', ''),
                        'link': item.get('link', ''),
                        'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)).isoformat(),
                        'summary': item.get('summary', '')
                    })
                
                # Debug logging
                print(f"Yahoo Finance news response for {symbol}:")
                print(f"  News items: {len(processed_news)}")
                if processed_news:
                    print(f"  First news title: {processed_news[0].get('title', 'No title')}")
                    
                return processed_news
                
            except (AttributeError, TypeError, json.JSONDecodeError) as news_error:
                print(f"Invalid news format from Yahoo Finance for {symbol}: {news_error}")
                return []
                
        except Exception as e:
            retries += 1
            print(f"Error fetching news from Yahoo Finance for {symbol} (attempt {retries}/{max_retries}): {e}")
            if retries >= max_retries:
                print(f"Failed to fetch news after {max_retries} attempts")
                return []
            # Add exponential backoff
            time.sleep(retries * 2)

def get_stock_fundamentals(symbol, max_retries=3):
    """Get fundamental data for a stock using Alpha Vantage as primary source"""
    # Import Alpha Vantage utils
    from utils.alpha_vantage_utils import fetch_alpha_vantage_fundamentals
    
    print(f"Fetching fundamentals for {symbol} from Alpha Vantage...")
    alpha_vantage_fundamentals = fetch_alpha_vantage_fundamentals(symbol)
    
    # Debug logging
    print(f"Alpha Vantage fundamentals response for {symbol}:")
    has_income = "income_statement" in alpha_vantage_fundamentals and alpha_vantage_fundamentals["income_statement"]
    has_balance = "balance_sheet" in alpha_vantage_fundamentals and alpha_vantage_fundamentals["balance_sheet"]
    has_cash = "cash_flow" in alpha_vantage_fundamentals and alpha_vantage_fundamentals["cash_flow"]
    has_earnings = "earnings" in alpha_vantage_fundamentals and alpha_vantage_fundamentals["earnings"]
    
    print(f"  Has income statement: {has_income}")
    print(f"  Has balance sheet: {has_balance}")
    print(f"  Has cash flow: {has_cash}")
    print(f"  Has earnings: {has_earnings}")
    
    # Check if we got meaningful data from Alpha Vantage
    if any([has_income, has_balance, has_cash, has_earnings]):
        return alpha_vantage_fundamentals
    
    # If Alpha Vantage failed, try Yahoo Finance as fallback
    print(f"No meaningful fundamentals from Alpha Vantage for {symbol}, trying Yahoo Finance as fallback...")
    retries = 0
    
    while retries < max_retries:
        try:
            # Add delay to avoid hitting rate limits
            if retries > 0:
                delay = 2 + random.random() * 3  # Random delay between 2-5 seconds
                time.sleep(delay)
                
            stock = yf.Ticker(symbol)
            
            try:
                # Get financial data
                balance_sheet = stock.balance_sheet
                income_stmt = stock.income_stmt
                cash_flow = stock.cashflow
                
                # Process data for agent consumption without recommendations
                fundamentals = {
                    'balance_sheet': balance_sheet.to_dict() if not balance_sheet.empty else {},
                    'income_statement': income_stmt.to_dict() if not income_stmt.empty else {},
                    'cash_flow': cash_flow.to_dict() if not cash_flow.empty else {}
                }
                
                # Try to get recommendations, but don't fail if they're not available
                try:
                    recommendations = stock.recommendations
                    if recommendations is not None and not recommendations.empty:
                        fundamentals['recommendations'] = recommendations.to_dict()
                except Exception as rec_error:
                    print(f"Could not fetch recommendations from Yahoo Finance for {symbol}: {rec_error}")
                
                # Debug logging
                has_income = bool(fundamentals.get('income_statement'))
                has_balance = bool(fundamentals.get('balance_sheet'))
                has_cash = bool(fundamentals.get('cash_flow'))
                has_recs = bool(fundamentals.get('recommendations'))
                
                print(f"Yahoo Finance fundamentals response for {symbol}:")
                print(f"  Has income statement: {has_income}")
                print(f"  Has balance sheet: {has_balance}")
                print(f"  Has cash flow: {has_cash}")
                print(f"  Has recommendations: {has_recs}")
                
                return fundamentals
                    
            except Exception as inner_error:
                print(f"Error processing Yahoo Finance fundamentals for {symbol}: {inner_error}")
                return {}
                
        except Exception as e:
            retries += 1
            print(f"Error fetching fundamentals from Yahoo Finance for {symbol} (attempt {retries}/{max_retries}): {e}")
            if retries >= max_retries:
                print(f"Failed to fetch fundamentals after {max_retries} attempts")
                return {}
            # Add exponential backoff
            time.sleep(retries * 2)
