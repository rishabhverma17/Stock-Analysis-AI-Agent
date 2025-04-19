"""
Visualization Agent - Responsible for creating charts and visualizations of stock data
"""

import os
import json
from typing import Dict, Any, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from agents.base_agent import BaseAgent

class VisualizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="VisualizationAgent")
        self.system_prompt = """
        You are a data visualization agent specialized in financial charts. 
        Your task is to create clear, informative, and visually appealing charts 
        that effectively communicate stock performance and analysis results.
        Focus on highlighting key patterns and insights that support the analysis.
        """
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the analysis data and create visualizations.
        
        Args:
            input_data: Dictionary containing analysis results from AnalysisAgent
            
        Returns:
            Dictionary with visualization data
        """
        self.update_status("processing")
        
        try:
            print("\n" + "="*50)
            print("VISUALIZATION AGENT - DEBUG INFO")
            print("="*50)
            
            # Check if input data is valid
            if not input_data.get('success', False):
                raise ValueError("Invalid input data")
            
            try:
                # Extract basic information
                symbol = input_data.get('symbol', '')
                period = input_data.get('period_description', '')
                recommendation = input_data.get('recommendation', 'HOLD')
                confidence = input_data.get('confidence', 'LOW')
                
                print(f"Processing data for symbol: {symbol}, period: {period}")
            except Exception as e:
                print(f"ERROR in basic info extraction: {str(e)}")
                raise
            
            try:
                # Get company info
                company_info = input_data.get('company_info', {})
                if not company_info:
                    # Try to get it from historical_data.info as backup
                    historical_data_obj = input_data.get('historical_data', {})
                    if isinstance(historical_data_obj, dict):
                        company_info = historical_data_obj.get('info', {})
                
                print(f"Company info found: {bool(company_info)}")
            except Exception as e:
                print(f"ERROR in company info extraction: {str(e)}")
                raise
            
            try:
                # Get chart data - try multiple sources
                chart_data = self._get_chart_data(input_data)
                print(f"Chart data found: {len(chart_data)} points")
                
                if not chart_data:
                    raise ValueError("No chart data available for visualization")
            except Exception as e:
                print(f"ERROR in chart data extraction: {str(e)}")
                raise
            
            try:
                # Extract dates, prices, etc. from chart data
                chart_series = self._extract_chart_series(chart_data)
                print(f"Chart series extracted with {len(chart_series['dates'])} dates")
            except Exception as e:
                print(f"ERROR in chart series extraction: {str(e)}")
                raise
            
            try:
                # Create chart configuration
                self.update_status("creating price chart")
                chart_config = self._create_chart_config(
                    symbol=symbol,
                    company_name=company_info.get('longName', symbol),
                    period=period,
                    recommendation=recommendation,
                    confidence=confidence,
                    chart_series=chart_series
                )
                print("Chart config created successfully")
            except Exception as e:
                print(f"ERROR in chart config creation: {str(e)}")
                raise
            
            # Get visualization insights from Ollama
            prompt = f"""
            I've created a stock chart for {symbol} ({company_info.get('longName', symbol)}) over {period}.
            The chart shows the price history and volume, along with any available technical indicators.
            
            The analysis resulted in a {recommendation} recommendation with {confidence} confidence.
            
            Provide a brief description of what key patterns or insights should be highlighted in this visualization.
            Explain what a viewer should focus on when looking at this chart and how it supports the {recommendation} recommendation.
            Keep your response under 150 words.
            """
            
            viz_insights = self._call_ollama(prompt, self.system_prompt)
            
            # Prepare output
            result = {
                "success": True,
                "symbol": symbol,
                "period": input_data.get('period'),
                "period_description": period,
                "company_info": company_info,
                "recommendation": recommendation,
                "confidence": confidence,
                "chart_config": chart_config,
                "visualization_insights": viz_insights,
                "timestamp": datetime.now().isoformat()
            }
            
            self.result = result
            self.update_status("completed")
            return result
            
        except Exception as e:
            self.error = str(e)
            self.update_status("error")
            return {"success": False, "error": self.error}
    
    def _get_chart_data(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract chart data from various possible locations in the input data"""
        # Try direct chart_data field first
        chart_data = input_data.get('chart_data', [])
        if chart_data:
            return chart_data
        
        # Try historical_data.data next
        historical_data = input_data.get('historical_data', {})
        if isinstance(historical_data, dict) and 'data' in historical_data:
            return historical_data['data']
        
        # If we're here, we couldn't find chart data
        return []
    
    def _extract_chart_series(self, chart_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract the series data from the chart data points with case-insensitive field matching"""
        dates = []
        prices = []
        volumes = []
        opens = []
        highs = []
        lows = []
        ma20 = []
        ma50 = []
        
        # Case-insensitive field mapping
        field_map = {
            'date': ['date', 'Date'],
            'close': ['close', 'Close'],
            'volume': ['volume', 'Volume'],
            'open': ['open', 'Open'],
            'high': ['high', 'High'],
            'low': ['low', 'Low'],
            'ma20': ['ma20', 'MA20'],
            'ma50': ['ma50', 'MA50']
        }
        
        for point in chart_data:
            # Get each field with case-insensitive matching
            for field, variants in field_map.items():
                value = None
                for variant in variants:
                    if variant in point:
                        value = point[variant]
                        break
                
                # Assign extracted value to the appropriate list
                if field == 'date':
                    dates.append(value)
                elif field == 'close':
                    prices.append(value)
                elif field == 'volume':
                    volumes.append(value)
                elif field == 'open':
                    opens.append(value)
                elif field == 'high':
                    highs.append(value)
                elif field == 'low':
                    lows.append(value)
                elif field == 'ma20':
                    if value is not None:
                        ma20.append(value)
                elif field == 'ma50':
                    if value is not None:
                        ma50.append(value)
        
        return {
            'dates': dates,
            'prices': prices,
            'volumes': volumes,
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'ma20': ma20,
            'ma50': ma50
        }
    
    def _create_chart_config(self, symbol, company_name, period, recommendation, 
                            confidence, chart_series) -> Dict[str, Any]:
        """Create the chart configuration for the UI"""
        return {
            "type": "candlestick",
            "symbol": symbol,
            "company_name": company_name,
            "period": period,
            "recommendation": recommendation,
            "confidence": confidence,
            "data": {
                "dates": chart_series['dates'],
                "prices": chart_series['prices'],
                "volumes": chart_series['volumes'],
                "opens": chart_series['opens'],
                "highs": chart_series['highs'],
                "lows": chart_series['lows'],
                "has_ma20": len(chart_series['ma20']) > 0,
                "has_ma50": len(chart_series['ma50']) > 0,
                "ma20": chart_series['ma20'],
                "ma50": chart_series['ma50']
            }
        }
