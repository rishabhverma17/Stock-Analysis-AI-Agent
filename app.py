"""
Main application file for the Chain of Agents stock analysis system
"""

import os
import json
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime

from agents.data_collector_agent import DataCollectorAgent
from agents.analysis_agent import AnalysisAgent
from agents.visualization_agent import VisualizationAgent
from config import PORT, DEBUG, TIME_PERIODS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Flask to ignore TLS handshake errors
try:
    # This helps avoid TLS handshake issues in development
    import werkzeug.serving
    # Patch the werkzeug server to ignore certain SSL errors
    original_handle_error = werkzeug.serving.WSGIRequestHandler.handle_one_request
    
    def patched_handle_error(*args, **kwargs):
        try:
            return original_handle_error(*args, **kwargs)
        except (ConnectionError, BrokenPipeError) as e:
            logger.warning(f"Connection error (probably SSL/TLS handshake): {e}")
            return
    
    werkzeug.serving.WSGIRequestHandler.handle_one_request = patched_handle_error
    logger.info("Patched Flask server to handle SSL/TLS errors")
except ImportError:
    logger.warning("Could not patch Flask server for SSL/TLS errors")

app = Flask(__name__, static_folder='ui/static', template_folder='ui/templates')

# Initialize agents
data_collector = DataCollectorAgent()
analysis_agent = AnalysisAgent()
visualization_agent = VisualizationAgent()

@app.route('/')
def index():
    """Render the main application page"""
    time_periods = [{"value": k, "label": v} for k, v in TIME_PERIODS.items()]
    return render_template('index.html', time_periods=time_periods)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint to analyze a stock"""
    data = request.json
    symbol = data.get('symbol', '').strip().upper()
    period = data.get('period', '1y')
    
    if not symbol:
        return jsonify({
            'success': False,
            'error': 'Stock symbol is required'
        })
    
    # Initialize pipeline status
    pipeline_status = {
        'data_collection': {
            'name': data_collector.name,
            'status': 'pending',
            'start_time': None,
            'end_time': None
        },
        'analysis': {
            'name': analysis_agent.name,
            'status': 'pending',
            'start_time': None,
            'end_time': None
        },
        'visualization': {
            'name': visualization_agent.name,
            'status': 'pending',
            'start_time': None,
            'end_time': None
        }
    }
    
    try:
        # Step 1: Collect data
        pipeline_status['data_collection']['status'] = 'running'
        pipeline_status['data_collection']['start_time'] = datetime.now().isoformat()
        
        data_result = data_collector.process({
            'symbol': symbol,
            'period': period
        })
        
        pipeline_status['data_collection']['status'] = 'completed' if data_result.get('success', False) else 'error'
        pipeline_status['data_collection']['end_time'] = datetime.now().isoformat()
        
        if not data_result.get('success', False):
            return jsonify({
                'success': False,
                'error': data_result.get('error', 'Failed to collect stock data'),
                'pipeline_status': pipeline_status
            })
        
        # Step 2: Analyze data
        pipeline_status['analysis']['status'] = 'running'
        pipeline_status['analysis']['start_time'] = datetime.now().isoformat()
        
        analysis_result = analysis_agent.process(data_result)
        
        pipeline_status['analysis']['status'] = 'completed' if analysis_result.get('success', False) else 'error'
        pipeline_status['analysis']['end_time'] = datetime.now().isoformat()
        
        if not analysis_result.get('success', False):
            return jsonify({
                'success': False,
                'error': analysis_result.get('error', 'Failed to analyze stock data'),
                'pipeline_status': pipeline_status
            })
        
        # Step 3: Create visualization
        pipeline_status['visualization']['status'] = 'running'
        pipeline_status['visualization']['start_time'] = datetime.now().isoformat()
        
        visualization_result = visualization_agent.process(analysis_result)
        
        pipeline_status['visualization']['status'] = 'completed' if visualization_result.get('success', False) else 'error'
        pipeline_status['visualization']['end_time'] = datetime.now().isoformat()
        
        if not visualization_result.get('success', False):
            return jsonify({
                'success': False,
                'error': visualization_result.get('error', 'Failed to create visualization'),
                'pipeline_status': pipeline_status
            })
        
        # Return combined results
        return jsonify({
            'success': True,
            'symbol': symbol,
            'period': period,
            'period_description': TIME_PERIODS.get(period, ''),
            'company_info': visualization_result.get('company_info', {}),
            'recommendation': visualization_result.get('recommendation', 'HOLD'),
            'confidence': visualization_result.get('confidence', 'LOW'),
            'analysis': analysis_result.get('analysis', ''),
            'chart_config': visualization_result.get('chart_config', {}),
            'visualization_insights': visualization_result.get('visualization_insights', ''),
            'pipeline_status': pipeline_status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'pipeline_status': pipeline_status
        })

@app.route('/api/status')
def status():
    """API endpoint to check status of all agents"""
    return jsonify({
        'data_collector': data_collector.to_dict(),
        'analysis_agent': analysis_agent.to_dict(),
        'visualization_agent': visualization_agent.to_dict()
    })

if __name__ == '__main__':
    # Add a message about the TLS errors to help with troubleshooting
    print("\n" + "-"*80)
    print("NOTE: You may see 'Bad request version' errors in the logs.")
    print("These are SSL/TLS handshake attempts that can be safely ignored.")
    print("The application is functioning normally despite these error messages.")
    print("-"*80 + "\n")
    
    # Run the Flask app with a simpler configuration that reduces TLS errors
    app.run(host='127.0.0.1', port=PORT, debug=DEBUG)
