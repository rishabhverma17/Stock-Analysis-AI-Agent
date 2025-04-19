"""
Alternative data sources for stock information when primary sources are rate-limited
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime
import time

def fetch_marketwatch_data(symbol, max_retries=2):
    """
    Fallback method to scrape basic stock data from MarketWatch
    
    This is a simple scraper for demonstration purposes
    """
    retries = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    while retries < max_retries:
        try:
            # Add delay between retries
            if retries > 0:
                time.sleep(3)
                
            url = f"https://www.marketwatch.com/investing/stock/{symbol}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get basic company info
            company_name = soup.select_one('h1.company__name')
            company_name = company_name.text.strip() if company_name else symbol
            
            # Get current price
            price_elem = soup.select_one('.intraday__price .value')
            current_price = float(price_elem.text.replace(',', '')) if price_elem else None
            
            # Get basic stats
            stats = {}
            stat_elements = soup.select('.key-stock-data .kv__item')
            for elem in stat_elements:
                label = elem.select_one('.label')
                value = elem.select_one('.primary')
                if label and value:
                    key = label.text.strip().lower().replace(' ', '_')
                    stats[key] = value.text.strip()
            
            # Create a minimal stock info object
            stock_info = {
                'symbol': symbol,
                'longName': company_name,
                'shortName': symbol,
                'currentPrice': current_price,
                'marketCap': stats.get('market_cap', None),
                'peRatio': stats.get('p/e_ratio', None),
                'dividend': stats.get('dividend', None),
                'yield': stats.get('yield', None),
                'dataSource': 'MarketWatch (Fallback)'
            }
            
            return {
                'success': True,
                'info': stock_info,
                'source': 'marketwatch'
            }
        
        except Exception as e:
            retries += 1
            print(f"Error fetching MarketWatch data for {symbol} (attempt {retries}/{max_retries}): {e}")
            if retries >= max_retries:
                return {
                    'success': False,
                    'error': str(e),
                    'source': 'marketwatch'
                }

def fetch_fmp_data(symbol, api_key=None):
    """
    Financial Modeling Prep API fallback method
    Requires an API key for full functionality, but has some free endpoints
    """
    try:
        # If no API key, use a limited free endpoint
        if not api_key:
            url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey=demo"
        else:
            url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={api_key}"
            
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            return {
                'success': False,
                'error': 'No data found',
                'source': 'fmp'
            }
            
        company_data = data[0]
        
        # Create a stock info object
        stock_info = {
            'symbol': symbol,
            'longName': company_data.get('companyName', symbol),
            'shortName': symbol,
            'sector': company_data.get('sector', ''),
            'industry': company_data.get('industry', ''),
            'website': company_data.get('website', ''),
            'currentPrice': company_data.get('price', None),
            'marketCap': company_data.get('mktCap', None),
            'peRatio': company_data.get('pe', None),
            'dividend': company_data.get('lastDiv', None),
            'dataSource': 'Financial Modeling Prep (Fallback)'
        }
        
        return {
            'success': True,
            'info': stock_info,
            'source': 'fmp'
        }
    
    except Exception as e:
        print(f"Error fetching FMP data for {symbol}: {e}")
        return {
            'success': False,
            'error': str(e),
            'source': 'fmp'
        }

def generate_basic_price_history(base_price, days=30, volatility=0.02):
    """
    Generate synthetic price data when historical data is unavailable
    This is for demonstration purposes when all data sources fail
    """
    import random
    import numpy as np
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
    dates.reverse()  # Oldest to newest
    
    # Generate random walk prices
    prices = [base_price]
    for i in range(1, days):
        change_percent = random.normalvariate(0, volatility)
        new_price = prices[-1] * (1 + change_percent)
        prices.append(new_price)
    
    # Generate volume (random)
    volumes = [int(random.uniform(500000, 5000000)) for _ in range(days)]
    
    # Create data points
    data_points = []
    for i in range(days):
        # Calculate high, low, open based on close
        close = prices[i]
        high = close * (1 + random.uniform(0, 0.015))
        low = close * (1 - random.uniform(0, 0.015))
        if i == 0:
            open_price = close * (1 - random.uniform(-0.01, 0.01))
        else:
            open_price = prices[i-1] * (1 + random.uniform(-0.01, 0.01))
            
        data_points.append({
            'Date': dates[i],
            'Open': round(open_price, 2),
            'High': round(high, 2),
            'Low': round(low, 2),
            'Close': round(close, 2),
            'Volume': volumes[i],
            'Synthetic': True  # Flag to indicate this is synthetic data
        })
    
    return data_points
