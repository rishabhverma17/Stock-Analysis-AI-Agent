"""
Base agent class for the Chain of Agents system
"""

import os
import json
import requests
import socket
import subprocess
from typing import Dict, Any, List, Optional

from config import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_API_ENDPOINT

class BaseAgent:
    def __init__(self, name: str, model: str = OLLAMA_MODEL):
        self.name = name
        self.model = model
        self.status = "idle"
        self.result = None
        self.error = None
    
    def _call_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call the Ollama API with the given prompt"""
        try:
            # Extract host and port from OLLAMA_HOST
            # Remove any protocol prefix and split host/port
            host_str = OLLAMA_HOST.replace("http://", "").replace("https://", "")
            if ":" in host_str:
                host, port_str = host_str.split(":")
                port = int(port_str)
            else:
                host = host_str
                port = 11434  # Default Ollama port
            
            # Prepare the request payload based on API endpoint
            if OLLAMA_API_ENDPOINT == "/api/generate":
                # Original format for /api/generate endpoint
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
                
                # Add system prompt if provided
                if system_prompt:
                    payload["system"] = system_prompt
            else:
                # Format for /api/chat endpoint
                messages = []
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                messages.append({
                    "role": "user",
                    "content": prompt
                })
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
            
            # Try all available methods to connect to Ollama
            data = None
            error_messages = []
            
            # Method 1: Try standard requests with explicit HTTP protocol
            try:
                print(f"Attempt 1: Using requests library with explicit HTTP...")
                url = f"http://{host}:{port}{OLLAMA_API_ENDPOINT}"
                response = requests.post(url, json=payload, timeout=30, verify=False)
                response.raise_for_status()
                data = response.json()
                print("Success with requests library!")
                
            except Exception as e:
                error_messages.append(f"Standard HTTP request failed: {str(e)}")
                
                # Method 2: Try with IP address instead of hostname
                try:
                    print(f"Attempt 2: Using requests with IP address...")
                    url = f"http://127.0.0.1:{port}{OLLAMA_API_ENDPOINT}"
                    response = requests.post(url, json=payload, timeout=30, verify=False)
                    response.raise_for_status()
                    data = response.json()
                    print("Success with IP address!")
                    
                except Exception as e:
                    error_messages.append(f"IP address HTTP request failed: {str(e)}")
                    
                    # Method 3: Try with subprocess curl command as last resort
                    try:
                        print(f"Attempt 3: Using curl subprocess...")
                        import subprocess
                        import json
                        
                        # Convert payload to JSON string
                        payload_str = json.dumps(payload)
                        
                        # Create curl command
                        curl_cmd = [
                            "curl", "-s",
                            "-X", "POST",
                            "-H", "Content-Type: application/json",
                            "-d", payload_str,
                            f"http://127.0.0.1:{port}{OLLAMA_API_ENDPOINT}"
                        ]
                        
                        # Execute curl command
                        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)
                        
                        if result.returncode != 0:
                            raise Exception(f"Curl failed with code {result.returncode}: {result.stderr}")
                            
                        # Parse the response
                        data = json.loads(result.stdout)
                        print("Success with curl command!")
                        
                    except Exception as e:
                        error_messages.append(f"Curl command failed: {str(e)}")
                        # If we get here, all methods have failed
                        raise Exception(f"All connection methods failed: {'; '.join(error_messages)}")
            
            # If we get here, one of the methods succeeded
            # Extract the response based on API endpoint
            if OLLAMA_API_ENDPOINT == "/api/generate":
                return data.get("response", "")
            else:
                # For /api/chat, the response is in a different format
                if isinstance(data, dict) and "message" in data:
                    return data["message"].get("content", "")
                # Log the actual response for debugging
                print(f"DEBUG: Ollama API response structure: {data}")
                return ""
            
        except requests.exceptions.ConnectionError as e:
            # Ollama server is not running or connection issues
            self.error = f"Ollama connection error at {OLLAMA_HOST}: {str(e)}"
            print(f"WARNING: {self.error}")
            
            # Check if this is an SSL/TLS handshake error
            if "SSLError" in str(e) or "handshake" in str(e).lower() or "protocol" in str(e).lower():
                print("This appears to be an SSL/TLS protocol error. Try changing OLLAMA_HOST in config.py.")
                
            return self._local_fallback(prompt, system_prompt)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Ollama server is running but endpoint not found
                self.error = f"Ollama API endpoint not found at {OLLAMA_HOST}/api/generate"
                print(f"WARNING: {self.error}")
                return self._local_fallback(prompt, system_prompt)
            else:
                self.error = str(e)
                print(f"ERROR: Ollama API returned {e}")
                return self._local_fallback(prompt, system_prompt)
        except Exception as e:
            self.error = str(e)
            print(f"ERROR: Failed to call Ollama API: {e}")
            return self._local_fallback(prompt, system_prompt)
    
    def _local_fallback(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Local fallback when Ollama is not available"""
        print(f"Using local fallback for {self.name} as Ollama is not available")
        
        # Simple rule-based responses when Ollama is unavailable
        if self.name == "DataCollectorAgent":
            return "I've collected the available data for this stock. Note that I'm operating in fallback mode since Ollama is not available. The data has been retrieved from alternative sources."
        
        elif self.name == "AnalysisAgent":
            recommendation = "HOLD"
            confidence = "LOW"
            
            if "BUY" in prompt or "buy" in prompt or "positive" in prompt or "increase" in prompt:
                recommendation = "BUY"
                confidence = "MEDIUM"
            elif "SELL" in prompt or "sell" in prompt or "negative" in prompt or "decrease" in prompt:
                recommendation = "SELL"
                confidence = "MEDIUM"
                
            return f"""
            Based on the available data, I can provide a basic analysis.
            
            The technical indicators show mixed signals, with some potential for growth but also some risk factors.
            
            Without access to the full AI capabilities (Ollama is offline), I'm providing a simplified analysis.
            
            RECOMMENDATION: {recommendation} (Confidence: {confidence})
            
            Note: For more detailed analysis, please ensure Ollama is running and the deepseek-coder:1.5b model is available.
            """
            
        elif self.name == "VisualizationAgent":
            return "I've created a visualization based on the available data. Note that I'm operating in fallback mode since Ollama is not available. The chart highlights the key price movements."
        
        else:
            return "I'm operating in fallback mode as the Ollama service is currently unavailable. Please start Ollama or check its configuration to enable full AI capabilities."
    
    def update_status(self, status: str) -> None:
        """Update the agent's status"""
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            "name": self.name,
            "model": self.model,
            "status": self.status,
            "has_result": self.result is not None,
            "has_error": self.error is not None
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and return the result.
        This method should be implemented by each agent subclass.
        """
        raise NotImplementedError("Each agent must implement the process method")
