"""LLM Service for SmartSOC Application

This module provides a centralized service for interacting with Large Language Models (LLMs)
for various tasks including regex generation, log type determination, and general queries.
"""

import time
import requests
import urllib3
from typing import Dict, Any, Tuple, Optional
from .base import BaseService
from .settings import settings_service


# LLM Task Prompts
GENERATE_PROMPT = """You are an expert in creating PCRE2 compatible regex patterns for log parsing. Given this log entry, analyze its structure and create a regex pattern with named capture groups that can parse similar logs.

Requirements:
1. Use PCRE2 compatible syntax
2. Include named capture groups for important fields (e.g., timestamp, ip, user, action, etc.)
3. Make the pattern flexible enough to match similar log entries
4. Use appropriate regex quantifiers and character classes
5. End the pattern with $ to match the entire line

Log entry to analyze:"""

FIX_PROMPT = """You are an expert in fixing PCRE2 regex patterns. The provided regex pattern does not fully match the log entry. Please analyze the issue and provide a corrected regex pattern.

Requirements:
1. Maintain PCRE2 compatibility
2. Keep existing named capture groups where possible
3. Fix any syntax errors or matching issues
4. Ensure the pattern matches the entire log entry

Please provide only the corrected regex pattern:"""

TYPING_PROMPT = """You are an expert in log analysis and classification. Given this log entry, determine the most appropriate log type and source type.

Respond in the format: "source_type, log_type"

Examples:
- For web server logs: "apache, access"
- For authentication logs: "system, auth"
- For firewall logs: "firewall, security"

Log entry to analyze:"""

SUGGEST_PROMPT = """You are an expert in cybersecurity log analysis. Given the log type and brand/technology, suggest the most appropriate category and classification.

Please respond in a clear, structured format.

Details to analyze:"""

TEST_PROMPT = "You are a helpful AI assistant. Please respond with a simple confirmation that you received this test message."


class LLMService(BaseService):
    """Service for interacting with Large Language Models."""
    
    def __init__(self):
        super().__init__('llm')
        self.temperature = 0.1  # Low temperature for consistent output
        
    def _get_active_llm_config(self) -> Optional[Dict[str, Any]]:
        """Get the configuration for the active LLM endpoint.
        
        Returns:
            Dictionary containing LLM configuration or None if not found
        """
        try:
            settings = settings_service.get_all_settings()
            active_endpoint_id = settings.get('llms', {}).get('active_endpoint')
            
            if not active_endpoint_id:
                self.log_warning("No active LLM endpoint configured")
                return None
                
            endpoints = settings.get('llms', {}).get('endpoints', [])
            for endpoint in endpoints:
                if endpoint.get('id') == active_endpoint_id:
                    return endpoint
                    
            self.log_warning(f"Active LLM endpoint '{active_endpoint_id}' not found in configuration")
            return None
            
        except Exception as e:
            self.log_error(f"Error getting active LLM config: {str(e)}", e)
            return None
    
    def _build_llm_payload(self, task: str, content: str, context: str = None, model: str = None) -> Dict[str, Any]:
        """Build the payload for LLM requests.
        
        Args:
            task: The task type (generate, fix, typing, suggest, test)
            content: The main content to process
            context: Additional context (e.g., regex for fix task)
            model: Override model name
            
        Returns:
            Dictionary containing the LLM request payload
        """
        # Define prompts for different tasks
        prompts = {
            "generate": (GENERATE_PROMPT, content),
            "fix": (FIX_PROMPT, f"Log: {content}\nRegex: {context}"),
            "typing": (TYPING_PROMPT, content),
            "suggest": (SUGGEST_PROMPT, f"Logtype: {content}\nBrand: {context}"),
            "test": (TEST_PROMPT, content)
        }
        
        if task not in prompts:
            raise ValueError(f"Invalid task: {task}")
        
        system_prompt, user_prompt = prompts[task]
        
        # Get model from config if not provided
        if not model:
            config = self._get_active_llm_config()
            model = config.get('model', 'default') if config else 'default'
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature
        }
        
        return payload
    
    def _send_llm_request(self, payload: Dict[str, Any], url: str = None) -> Tuple[str, int]:
        """Send request to LLM endpoint.
        
        Args:
            payload: The request payload
            url: Override URL for the request
            
        Returns:
            Tuple of (response_text, status_code)
        """
        # Get URL from config if not provided
        if not url:
            config = self._get_active_llm_config()
            if not config:
                return "No active LLM endpoint configured", 500
            url = config.get('url')
            
        if not url:
            return "No LLM endpoint URL configured", 500
        
        # Disable SSL warnings for internal requests
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        start_time = time.time()
        
        try:
            response = requests.post(url, json=payload, verify=False, timeout=30)
            response.raise_for_status()
            response_json = response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error occurred: {e}"
            self.log_error(error_msg)
            return error_msg, response.status_code if response else 500
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {e}"
            self.log_error(error_msg)
            return error_msg, 500
            
        except ValueError as e:
            error_msg = f"Invalid JSON response: {response.text[:100]}..."
            self.log_error(error_msg)
            return error_msg, response.status_code if response else 500
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        self.log_info(f"LLM request took {elapsed_time:.2f} seconds")
        
        # Extract response content based on different API formats
        reply = self._extract_response_content(response_json)
        
        # Clean up the output
        reply = self._clean_response(reply)
        
        return reply, response.status_code
    
    def _extract_response_content(self, response_json: Dict[str, Any]) -> str:
        """Extract content from different LLM API response formats.
        
        Args:
            response_json: The JSON response from the LLM API
            
        Returns:
            Extracted response text
        """
        # Try OpenAI format first
        choices = response_json.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if content:
                return content.strip()
        
        # Try Ollama format
        message = response_json.get("message", {})
        if message:
            content = message.get("content")
            if content:
                return content.strip()
        
        # Try direct response format
        if "response" in response_json:
            return response_json["response"].strip()
        
        # Fallback
        return response_json.get("text", "No response from LLM").strip()
    
    def _clean_response(self, response: str) -> str:
        """Clean up LLM response text.
        
        Args:
            response: Raw response text
            
        Returns:
            Cleaned response text
        """
        # Remove code block markers
        response = response.replace("```", "")
        
        # Remove regex prefix if present
        if response.startswith("regex"):
            response = response[len("regex"):].strip()
        
        # Remove newlines
        response = response.replace("\n", "")
        
        return response.strip()
    
    def generate_regex(self, log_entry: str, fix_count: int = 3) -> Dict[str, Any]:
        """Generate regex pattern for a log entry using LLM.
        
        Args:
            log_entry: The log entry to generate regex for
            fix_count: Number of fix iterations to attempt
            
        Returns:
            Dictionary with success status, regex, and error message
        """
        try:
            self.log_info(f"Generating regex for log entry")
            
            # Initial regex generation
            payload = self._build_llm_payload("generate", log_entry)
            regex, status_code = self._send_llm_request(payload)
            
            if status_code != 200:
                return {
                    'success': False,
                    'error': f"Failed to generate regex: HTTP {status_code}",
                    'regex': ''
                }
            
            # Ensure regex ends with $
            if not regex.endswith("$"):
                regex += "$"
            
            self.log_info(f"Generated regex: {regex[:100]}...")
            
            return {
                'success': True,
                'regex': regex,
                'error': None
            }
            
        except Exception as e:
            error_msg = f"Error generating regex: {str(e)}"
            self.log_error(error_msg, e)
            return {
                'success': False,
                'error': error_msg,
                'regex': ''
            }
    
    def determine_log_type(self, log_entry: str) -> Dict[str, Any]:
        """Determine log type and source type for a log entry.
        
        Args:
            log_entry: The log entry to analyze
            
        Returns:
            Dictionary with success status, result, and error message
        """
        try:
            self.log_info("Determining log type for entry")
            
            payload = self._build_llm_payload("typing", log_entry)
            response, status_code = self._send_llm_request(payload)
            
            if status_code != 200:
                return {
                    'success': False,
                    'error': f"Failed to determine log type: HTTP {status_code}",
                    'result': ''
                }
            
            self.log_info(f"Determined log type: {response}")
            
            return {
                'success': True,
                'result': response,
                'error': None
            }
            
        except Exception as e:
            error_msg = f"Error determining log type: {str(e)}"
            self.log_error(error_msg, e)
            return {
                'success': False,
                'error': error_msg,
                'result': ''
            }
    
    def test_connection(self, url: str = None, model: str = None) -> Dict[str, Any]:
        """Test connection to LLM endpoint.
        
        Args:
            url: Override URL for testing
            model: Override model for testing
            
        Returns:
            Dictionary with success status and response details
        """
        try:
            self.log_info("Testing LLM connection")
            
            payload = self._build_llm_payload("test", "Hello, this is a test message", model=model)
            response, status_code = self._send_llm_request(payload, url)
            
            success = status_code == 200 and len(response.strip()) > 0
            
            return {
                'success': success,
                'status_code': status_code,
                'response': response,
                'error': None if success else f"HTTP {status_code}: {response}"
            }
            
        except Exception as e:
            error_msg = f"Error testing LLM connection: {str(e)}"
            self.log_error(error_msg, e)
            return {
                'success': False,
                'status_code': 500,
                'response': '',
                'error': error_msg
            }
    
    def query_llm(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """Send a general query to the LLM.
        
        Args:
            prompt: The prompt/query to send
            model: Override model for the request
            
        Returns:
            Dictionary with success status and response details
        """
        try:
            self.log_info("Sending general query to LLM")
            
            # Use test task for general queries
            payload = self._build_llm_payload("test", prompt, model=model)
            response, status_code = self._send_llm_request(payload)
            
            success = status_code == 200
            
            return {
                'success': success,
                'status_code': status_code,
                'response': response,
                'error': None if success else f"HTTP {status_code}: {response}"
            }
            
        except Exception as e:
            error_msg = f"Error querying LLM: {str(e)}"
            self.log_error(error_msg, e)
            return {
                'success': False,
                'status_code': 500,
                'response': '',
                'error': error_msg
            }


# Create service instance
llm_service = LLMService()