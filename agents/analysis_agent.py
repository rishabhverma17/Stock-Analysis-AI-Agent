"""
Analysis Agent - Responsible for analyzing stock data and making recommendations
"""

import os
import json
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime

from agents.base_agent import BaseAgent

class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AnalysisAgent")
        self.system_prompt = """
        You are a sophisticated financial analysis agent. Your task is to analyze stock market data
        and provide insightful recommendations. Consider technical indicators, fundamental analysis,
        recent news sentiment, and market trends. Be balanced in your analysis, highlighting both
        potential risks and opportunities. Provide a clear buy, sell, or hold recommendation with
        supporting evidence and reasoning.
        """
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the stock data and perform analysis.
        
        Args:
            input_data: Dictionary containing collected stock data from DataCollectorAgent
            
        Returns:
            Dictionary with analysis results
        """
        self.update_status("processing")
        
        try:
            # Debug: Log the structure of input data
            print("\n" + "="*50)
            print("ANALYSIS AGENT - DEBUG INFO")
            print("="*50)
            print(f"Input data keys: {list(input_data.keys())}")
            
            # Check if input data is valid
            if not input_data.get('success', False):
                print("ERROR: Input data missing 'success' flag or it's False")
                raise ValueError("Invalid input data")
            
            symbol = input_data.get('symbol', '')
            period = input_data.get('period_description', '')
            
            # Debug historical data structure
            historical_data_obj = input_data.get('historical_data', {})
            print(f"Historical data object keys: {list(historical_data_obj.keys()) if isinstance(historical_data_obj, dict) else 'Not a dict'}")
            
            historical_data = historical_data_obj.get('data', [])
            print(f"Historical data length: {len(historical_data)}")
            
            # Debug chart_data as alternative
            chart_data = input_data.get('chart_data', [])
            print(f"Chart data length: {len(chart_data)}")
            
            # Check which data source to use
            if not historical_data and chart_data:
                print("Using chart_data instead of historical_data")
                historical_data = chart_data
            
            company_info = input_data.get('historical_data', {}).get('info', {})
            if not company_info:
                # Try to get it from the alternative field
                company_info = input_data.get('company_info', {})
                print(f"Using alternative company_info, found: {bool(company_info)}")
                
            news = input_data.get('news', [])
            fundamentals = input_data.get('fundamentals', {})
            
            # Convert historical data to dataframe for analysis
            if not historical_data:
                print("ERROR: No historical data available for analysis")
                print(f"Input data dump: {json.dumps(input_data, indent=2)[:500]}...")
                raise ValueError("No historical data available for analysis")
            
            print(f"First record in historical data: {json.dumps(historical_data[0], indent=2) if historical_data else 'None'}")
            print("="*50)
            
            df = pd.DataFrame(historical_data)
            
            # Calculate basic technical indicators
            self.update_status("calculating technical indicators")
            
            # Convert Date column to datetime if it's not already
            if 'Date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['Date']):
                df['Date'] = pd.to_datetime(df['Date'])
            
            # Calculate moving averages
            if len(df) >= 50:
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['MA50'] = df['Close'].rolling(window=50).mean()
                
                # Calculate if price is above moving averages
                latest_close = df['Close'].iloc[-1]
                ma20_signal = "above" if latest_close > df['MA20'].iloc[-1] else "below"
                ma50_signal = "above" if latest_close > df['MA50'].iloc[-1] else "below"
                
                # Calculate RSI (Relative Strength Index)
                delta = df['Close'].diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                rs = avg_gain / avg_loss
                df['RSI'] = 100 - (100 / (1 + rs))
                
                # Get latest RSI value
                latest_rsi = df['RSI'].iloc[-1]
                
                # Calculate price trend
                recent_trend = "uptrend" if df['Close'].iloc[-10:].mean() > df['Close'].iloc[-20:-10].mean() else "downtrend"
                
                # Prepare technical analysis summary
                technical_analysis = {
                    "latest_close": latest_close,
                    "ma20_signal": ma20_signal,
                    "ma50_signal": ma50_signal,
                    "rsi": latest_rsi,
                    "trend": recent_trend
                }
            else:
                technical_analysis = {
                    "error": "Not enough data points for technical analysis"
                }
            
            # Prepare the data for the language model analysis
            self.update_status("generating analysis and recommendation")
            
            # Create a text representation of the data for the language model
            company_desc = f"Company: {company_info.get('longName', symbol)}"
            if company_info.get('sector'):
                company_desc += f"\nSector: {company_info.get('sector')}"
            if company_info.get('industry'):
                company_desc += f"\nIndustry: {company_info.get('industry')}"
            
            # Technical indicators summary
            tech_summary = "Technical Analysis:\n"
            if 'error' not in technical_analysis:
                tech_summary += f"- Current Price: ${technical_analysis['latest_close']:.2f}\n"
                tech_summary += f"- Price is {technical_analysis['ma20_signal']} the 20-day moving average\n"
                tech_summary += f"- Price is {technical_analysis['ma50_signal']} the 50-day moving average\n"
                tech_summary += f"- RSI: {technical_analysis['rsi']:.2f} (Oversold < 30, Overbought > 70)\n"
                tech_summary += f"- Recent Price Trend: {technical_analysis['trend']}\n"
            else:
                tech_summary += f"- {technical_analysis['error']}\n"
            
            # Fundamentals summary
            fund_summary = "Fundamental Analysis:\n"
            if company_info.get('marketCap'):
                fund_summary += f"- Market Cap: ${company_info.get('marketCap') / 1e9:.2f} billion\n"
            if company_info.get('trailingPE'):
                fund_summary += f"- P/E Ratio: {company_info.get('trailingPE'):.2f}\n"
            if company_info.get('dividendYield'):
                fund_summary += f"- Dividend Yield: {company_info.get('dividendYield')*100:.2f}%\n"
            
            # News summary
            news_summary = "Recent News:\n"
            for article in news[:3]:  # Limit to top 3 news articles
                news_summary += f"- {article.get('title')}\n"
            
            # Price history summary
            price_summary = "Price Performance:\n"
            if len(df) > 0:
                first_price = df['Close'].iloc[0]
                last_price = df['Close'].iloc[-1]
                percent_change = ((last_price - first_price) / first_price) * 100
                price_summary += f"- {period} Change: {percent_change:.2f}%\n"
                
                if len(df) >= 30:
                    month_change = ((last_price - df['Close'].iloc[-30]) / df['Close'].iloc[-30]) * 100
                    price_summary += f"- 1 Month Change: {month_change:.2f}%\n"
                
            # Prepare the prompt for the language model
            prompt = f"""
            I need to analyze the following stock data for {symbol} and provide a buy, sell, or hold recommendation.
            
            {company_desc}
            
            {tech_summary}
            
            {fund_summary}
            
            {news_summary}
            
            {price_summary}
            
            Based on the data above, provide a detailed analysis of {symbol} with the following:
            1. A summary of key strengths and weaknesses
            2. Evaluation of technical indicators
            3. Assessment of fundamental factors
            4. Analysis of recent news impact
            5. Clear buy, sell, or hold recommendation with confidence level (high, medium, low)
            6. Brief explanation of the reasoning behind the recommendation
            
            Format your recommendation prominently at the end as "RECOMMENDATION: [BUY/SELL/HOLD] (Confidence: [HIGH/MEDIUM/LOW])"
            """
            
            # Get analysis from Ollama
            analysis = self._call_ollama(prompt, self.system_prompt)
            
            # Extract recommendation
            recommendation = "HOLD"  # Default
            confidence = "LOW"      # Default
            
            # Try to extract recommendation from the analysis text
            if "RECOMMENDATION:" in analysis:
                rec_part = analysis.split("RECOMMENDATION:")[1].strip()
                if "BUY" in rec_part[:20]:
                    recommendation = "BUY"
                elif "SELL" in rec_part[:20]:
                    recommendation = "SELL"
                elif "HOLD" in rec_part[:20]:
                    recommendation = "HOLD"
                    
                # Extract confidence
                if "Confidence:" in rec_part:
                    conf_part = rec_part.split("Confidence:")[1].strip()
                    if "HIGH" in conf_part[:10]:
                        confidence = "HIGH"
                    elif "MEDIUM" in conf_part[:10]:
                        confidence = "MEDIUM"
                    elif "LOW" in conf_part[:10]:
                        confidence = "LOW"
            
            # Prepare chart data
            chart_data = []
            for row in historical_data:
                chart_point = {
                    "date": row.get("Date"),
                    "close": row.get("Close"),
                    "volume": row.get("Volume")
                }
                if "MA20" in df.columns:
                    idx = df[df["Date"] == row.get("Date")].index
                    if not idx.empty and not pd.isna(df.loc[idx[0], "MA20"]):
                        chart_point["ma20"] = df.loc[idx[0], "MA20"]
                if "MA50" in df.columns:
                    idx = df[df["Date"] == row.get("Date")].index
                    if not idx.empty and not pd.isna(df.loc[idx[0], "MA50"]):
                        chart_point["ma50"] = df.loc[idx[0], "MA50"]
                chart_data.append(chart_point)
            
            # Prepare output
            result = {
                "success": True,
                "symbol": symbol,
                "period": input_data.get('period'),
                "period_description": period,
                "company_info": company_info,
                "analysis": analysis,
                "recommendation": recommendation,
                "confidence": confidence,
                "technical_indicators": technical_analysis,
                "chart_data": chart_data,
                "timestamp": datetime.now().isoformat()
            }
            
            self.result = result
            self.update_status("completed")
            return result
            
        except Exception as e:
            self.error = str(e)
            self.update_status("error")
            return {"success": False, "error": self.error}
