"""
REST API Connector Node - Makes HTTP calls to external REST APIs
"""
import json
import aiohttp
import ssl
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from app.workflow.base import WorkflowNode
from app.core.logging import logger


class RestApiNode(WorkflowNode):
    """REST API connector node that makes HTTP calls to configured endpoints"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None, rest_api_service=None, llm_service=None):
        super().__init__(node_id, config)
        self.rest_api_service = rest_api_service
        self.llm_service = llm_service
        self.rest_api_entity = None
        self.llm_entity = None
        self.rest_api_initialized = False
        self.llm_initialized = False
        logger.info(f"[DEV] RestApiNode initialized - ID: {node_id}")
        logger.info(f"[DEV] RestApiNode config: {self.config}")
    
    async def _fetch_rest_api_entity(self):
        """Fetch REST API entity from ControlTower using injected RestAPIService"""
        if self.rest_api_initialized:
            return
            
        if not self.rest_api_service:
            raise ValueError("RestAPIService not provided. Make sure to inject RestAPIService in constructor.")
            
        # Get REST API ID from config (now includes root-level fields like 'link')
        rest_api_id = self.get_link() or self.config.get("rest_api_id")
        logger.info(f"[DEV] RestApiNode - Extracted REST API ID: {rest_api_id}")
        
        if not rest_api_id:
            logger.error(f"[DEV] RestApiNode - No REST API ID found. Config: {self.config}")
            raise ValueError("REST API ID not found in node configuration. Expected 'link' or 'rest_api_id' field.")
        
        # Get REST API through injected service
        try:
            self.rest_api_entity = await self.rest_api_service.get_by_id(rest_api_id)
        except Exception as e:
            logger.error(f"[DEV] RestApiNode - Failed to fetch REST API: {e}")
            raise ValueError(f"Failed to fetch REST API: {e}")
            
        if not self.rest_api_entity:
            raise ValueError(f"REST API with ID {rest_api_id} not found")
            
        if not self.rest_api_entity.enabled:
            raise ValueError(f"REST API {self.rest_api_entity.name} is disabled")
            
        logger.info(f"[DEV] RestApiNode - Fetched REST API: {self.rest_api_entity.name} ({self.rest_api_entity.method} {self.rest_api_entity.endpoint_url})")
        self.rest_api_initialized = True

    async def _fetch_llm_entity(self):
        """Fetch LLM entity from ControlTower for intelligent request processing"""
        if self.llm_initialized:
            return
            
        # Get LLM ID from intel_link
        llm_id = self.get_intel_link()
        
        # If no intel_link is configured, skip LLM initialization (node will work without intelligence)
        if not llm_id:
            logger.info(f"[DEV] RestApiNode - No intel_link configured, proceeding without AI assistance")
            self.llm_initialized = True
            return
            
        if not self.llm_service:
            logger.warning(f"[DEV] RestApiNode - LLMService not provided, cannot use intel_link: {llm_id}")
            self.llm_initialized = True
            return
            
        # Get LLM through injected service
        try:
            self.llm_entity = await self.llm_service.get_by_id(llm_id)
        except Exception as e:
            logger.error(f"[DEV] RestApiNode - Failed to fetch LLM for intelligence: {e}")
            # Don't fail the entire node if LLM fetch fails, just proceed without intelligence
            self.llm_initialized = True
            return
            
        if not self.llm_entity:
            logger.warning(f"[DEV] RestApiNode - LLM with ID {llm_id} not found, proceeding without AI assistance")
        else:
            logger.info(f"[DEV] RestApiNode - Fetched LLM for intelligence: {self.llm_entity.name}")
            
        self.llm_initialized = True

    def _build_url(self, path_params: Dict[str, Any] = None) -> str:
        """Build the complete URL with path parameters"""
        base_url = self.rest_api_entity.base_url.rstrip('/')
        resource_path = self.rest_api_entity.resource_path or ''
        
        # Build the complete endpoint URL
        if resource_path:
            url = urljoin(base_url + '/', resource_path.lstrip('/'))
        else:
            url = base_url
            
        # Replace path parameters if provided
        if path_params:
            for key, value in path_params.items():
                url = url.replace(f'{{{key}}}', str(value))
                url = url.replace(f':{key}', str(value))  # Support :param format too
                
        return url

    def _prepare_headers(self, additional_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Prepare headers for the request"""
        headers = {}
        
        # Add configured headers
        if self.rest_api_entity.headers:
            headers.update(self.rest_api_entity.headers)
            
        # Add authentication headers
        if self.rest_api_entity.auth_headers:
            headers.update(self.rest_api_entity.auth_headers)
            
        # Add any additional headers from the state
        if additional_headers:
            headers.update(additional_headers)
            
        # Ensure Content-Type for POST/PUT/PATCH requests
        method = self.rest_api_entity.method.upper()
        if method in ['POST', 'PUT', 'PATCH'] and 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
            
        return headers

    def _prepare_params(self, query_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare query parameters for the request"""
        params = {}
        
        # Add configured query parameters
        if self.rest_api_entity.query_params:
            params.update(self.rest_api_entity.query_params)
            
        # Add any additional query params from the state
        if query_params:
            params.update(query_params)
            
        return params

    def _prepare_request_body(self, body_data: Any = None) -> Optional[str]:
        """Prepare request body for POST/PUT/PATCH requests"""
        method = self.rest_api_entity.method.upper()
        
        if method not in ['POST', 'PUT', 'PATCH']:
            return None
            
        if body_data is None:
            return None
            
        # If body_data is already a string, return as-is
        if isinstance(body_data, str):
            return body_data
            
        # Otherwise, serialize to JSON
        try:
            return json.dumps(body_data)
        except (TypeError, ValueError) as e:
            logger.error(f"[DEV] RestApiNode - Failed to serialize body data: {e}")
            raise ValueError(f"Failed to serialize request body: {e}")

    async def _intelligent_request_builder(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to intelligently build request parameters from state"""
        if not self.llm_entity:
            logger.error(f"[DEV] RestApiNode - No LLM available for intelligent processing, cannot proceed")
            raise ValueError("Intel_link LLM is required for intelligent request building but not configured")
        
        try:
            # Create a prompt for the LLM to analyze the state and build request parameters
            prompt = f"""
You are helping to build an HTTP request for a REST API call. Here's the context:

API Details:
- Method: {self.rest_api_entity.method}
- URL: {self.rest_api_entity.endpoint_url}
- Description: {getattr(self.rest_api_entity, 'description', 'No description available')}

Current Workflow State:
{json.dumps(state, indent=2)}

Instructions:
1. Analyze the workflow state and extract relevant data for the API call
2. Map the data to appropriate request components (path parameters, query parameters, headers, body)
3. Return ONLY a valid JSON object with these keys: "path_params", "query_params", "headers", "body_data"
4. Ensure all values are properly formatted for HTTP requests
5. If a parameter is not needed, set it to null or empty object

Example response format:
{{
    "path_params": {{"id": "123"}},
    "query_params": {{"limit": 10, "filter": "active"}},
    "headers": {{"Content-Type": "application/json"}},
    "body_data": {{"name": "example", "value": "test"}}
}}
"""

            logger.info(f"[DEV] RestApiNode - Using LLM for intelligent request building (LLM: {self.llm_entity.name})")
            logger.info(f"[DEV] RestApiNode - Prompt to LLM:\n{prompt}")
            
            # Call the LLM service to generate intelligent parameters
            llm_response = await self.llm_service.invoke(
                llm_entity=self.llm_entity,
                prompt=prompt
            )
            
            # Parse the LLM response as JSON
            try:
                intelligent_params = json.loads(llm_response.strip())
                logger.info(f"[DEV] RestApiNode - LLM-generated parameters: {intelligent_params}")
                
                # Validate the response has the required keys
                required_keys = ['path_params', 'query_params', 'headers', 'body_data']
                for key in required_keys:
                    if key not in intelligent_params:
                        intelligent_params[key] = None
                
                return intelligent_params
                
            except json.JSONDecodeError as e:
                logger.error(f"[DEV] RestApiNode - Failed to parse LLM response as JSON: {e}")
                logger.error(f"[DEV] RestApiNode - LLM Response: {llm_response}")
                raise ValueError(f"LLM returned invalid JSON response: {e}")
            
        except Exception as e:
            logger.error(f"[DEV] RestApiNode - Error in intelligent request building: {e}")
            raise ValueError(f"Intelligent request building failed: {e}")

    def _extract_path_params_intelligently(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently extract path parameters from state"""
        path_params = {}
        
        # Look for common ID patterns
        for key, value in state.items():
            if key.endswith('_id') or key == 'id':
                path_params[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key.endswith('_id') or sub_key == 'id':
                        path_params[sub_key] = sub_value
        
        return path_params

    def _extract_query_params_intelligently(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently extract query parameters from state"""
        query_params = {}
        
        # Look for filter, pagination, and search parameters
        filter_keys = ['filter', 'search', 'query', 'limit', 'page', 'size', 'sort', 'order']
        
        for key in filter_keys:
            if key in state:
                query_params[key] = state[key]
                
        # Check nested parameters
        if 'parameters' in state and isinstance(state['parameters'], dict):
            for key in filter_keys:
                if key in state['parameters']:
                    query_params[key] = state['parameters'][key]
        
        return query_params

    def _extract_headers_intelligently(self, state: Dict[str, Any]) -> Dict[str, str]:
        """Intelligently extract headers from state"""
        headers = {}
        
        # Standard headers from state
        if 'headers' in state and isinstance(state['headers'], dict):
            headers.update(state['headers'])
        
        # Add authentication if present
        if 'auth_token' in state:
            headers['Authorization'] = f"Bearer {state['auth_token']}"
        elif 'api_key' in state:
            headers['X-API-Key'] = state['api_key']
        
        return headers

    def _extract_body_data_intelligently(self, state: Dict[str, Any]) -> Any:
        """Intelligently extract body data from state"""
        # First check explicit body
        if 'body' in state:
            return state['body']
        
        # Check parameters.body
        if 'parameters' in state and isinstance(state['parameters'], dict):
            if 'body' in state['parameters']:
                return state['parameters']['body']
        
        # For POST/PUT/PATCH requests, try to build body from state
        method = self.rest_api_entity.method.upper()
        if method in ['POST', 'PUT', 'PATCH']:
            # Look for data that should be in the body
            body_data = {}
            exclude_keys = {'headers', 'path_params', 'query_params', 'parameters', 'response', 'status_code', 'success', 'error'}
            
            for key, value in state.items():
                if key not in exclude_keys and not key.endswith('_id') and key != 'id':
                    body_data[key] = value
            
            return body_data if body_data else None
        
        return None

    async def _make_http_request(self, url: str, method: str, headers: Dict[str, str] = None,
                                params: Dict[str, Any] = None, body: Optional[str] = None) -> Dict[str, Any]:
        """Make the actual HTTP request"""
        timeout = aiohttp.ClientTimeout(
            connect=self.config.get('timeout', 30),
            total=self.config.get('timeout', 30) * 2
        )
        
        # Configure SSL context for HTTPS requests
        ssl_context = None
        if url.startswith('https://'):
            ssl_context = ssl.create_default_context()
            # For development/testing, you might want to allow self-signed certificates
            # ssl_context.check_hostname = False
            # ssl_context.verify_mode = ssl.CERT_NONE
        
        retry_count = self.config.get('retry_count', 3)
        follow_redirects = self.config.get('follow_redirects', True)
        
        for attempt in range(retry_count + 1):
            try:
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    connector_owner=True
                ) as session:
                    
                    logger.info(f"[DEV] RestApiNode - Making {method} request to {url} (attempt {attempt + 1})")
                    
                    async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        data=body,
                        allow_redirects=follow_redirects
                    ) as response:
                        
                        # Read response content
                        try:
                            response_text = await response.text()
                            
                            # Try to parse as JSON, fallback to text
                            try:
                                response_data = json.loads(response_text) if response_text else None
                            except json.JSONDecodeError:
                                response_data = response_text
                                
                        except Exception as e:
                            logger.error(f"[DEV] RestApiNode - Failed to read response: {e}")
                            response_data = None
                        
                        result = {
                            'status_code': response.status,
                            'headers': dict(response.headers),
                            'data': response_data,
                            'url': str(response.url),
                            'method': method,
                            'success': 200 <= response.status < 300
                        }
                        
                        logger.info(f"[DEV] RestApiNode - Response status: {response.status}")
                        
                        # If successful or client error (4xx), don't retry
                        if response.status < 500:
                            return result
                            
                        # Server error (5xx) - might be worth retrying
                        if attempt < retry_count:
                            logger.warning(f"[DEV] RestApiNode - Server error {response.status}, retrying...")
                            continue
                        else:
                            return result
                            
            except aiohttp.ClientError as e:
                logger.error(f"[DEV] RestApiNode - HTTP client error (attempt {attempt + 1}): {e}")
                if attempt < retry_count:
                    continue
                else:
                    return {
                        'status_code': 0,
                        'headers': {},
                        'data': None,
                        'url': url,
                        'method': method,
                        'success': False,
                        'error': str(e)
                    }
            except Exception as e:
                logger.error(f"[DEV] RestApiNode - Unexpected error (attempt {attempt + 1}): {e}")
                if attempt < retry_count:
                    continue
                else:
                    return {
                        'status_code': 0,
                        'headers': {},
                        'data': None,
                        'url': url,
                        'method': method,
                        'success': False,
                        'error': str(e)
                    }

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the REST API call using intelligent request building"""
        try:
            # Fetch REST API configuration and LLM entity if not already done
            await self._fetch_rest_api_entity()
            await self._fetch_llm_entity()
            
            # Check if LLM is configured for intelligent request building
            intel_link = self.get_intel_link()
            if not intel_link or not self.llm_entity:
                error_msg = f"RestApiNode '{self.node_id}' requires an LLM configuration (intel_link) for intelligent request processing. Please configure an LLM in the node settings."
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'requires_llm': True
                }
            
            # Use intelligent request builder for all requests
            request_data = await self._intelligent_request_builder(state)
            path_params = request_data['path_params']
            query_params = request_data['query_params']
            headers = request_data['headers']
            body_data = request_data['body_data']
            
            logger.info(f"[DEV] RestApiNode - Processing request with path_params: {path_params}, query_params: {query_params}")
            
            # Build the complete URL
            url = self._build_url(path_params)
            
            # Prepare request components
            request_headers = self._prepare_headers(headers)
            request_params = self._prepare_params(query_params)
            request_body = self._prepare_request_body(body_data)
            
            # Make the HTTP request
            response = await self._make_http_request(
                url=url,
                method=self.rest_api_entity.method,
                headers=request_headers,
                params=request_params,
                body=request_body
            )
            
            # Update state with response
            new_state = state.copy()
            new_state['response'] = response['data']
            new_state['status_code'] = response['status_code']
            new_state['http_response'] = response  # Full response details
            
            # Set success flag
            new_state['success'] = response['success']
            
            logger.info(f"[DEV] RestApiNode - Request completed successfully: {response['success']}")
            
            return new_state
            
        except Exception as e:
            logger.error(f"[DEV] RestApiNode - Error processing request: {e}")
            
            # Return error state
            error_state = state.copy()
            error_state['response'] = None
            error_state['status_code'] = 0
            error_state['success'] = False
            error_state['error'] = str(e)
            
            return error_state
