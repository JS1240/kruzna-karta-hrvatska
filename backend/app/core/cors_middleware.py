"""
Custom CORS middleware to handle OPTIONS requests before parameter validation.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class CustomCORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware that handles OPTIONS requests immediately
    to prevent them from reaching route parameter validation.
    """
    
    def __init__(
        self,
        app,
        allow_origins: list = None,
        allow_credentials: bool = True,
        allow_methods: list = None,
        allow_headers: list = None,
        expose_headers: list = None,
        max_age: int = 600
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
        self.allow_headers = allow_headers or ["*"]
        self.expose_headers = expose_headers or []
        self.max_age = max_age
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Intercept requests and handle OPTIONS immediately.
        """
        # Handle OPTIONS requests immediately without calling next middleware/routes
        if request.method == "OPTIONS":
            return self._create_preflight_response(request)
        
        # For non-OPTIONS requests, proceed normally and add CORS headers to response
        response = await call_next(request)
        
        # Add CORS headers to actual responses
        self._add_cors_headers(response, request)
        
        return response
    
    def _create_preflight_response(self, request: Request) -> Response:
        """
        Create a preflight response for OPTIONS requests.
        """
        response = Response(status_code=200)
        
        # Add CORS headers
        self._add_cors_headers(response, request)
        
        # Add preflight-specific headers
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Max-Age"] = str(self.max_age)
        
        # Handle requested headers
        requested_headers = request.headers.get("Access-Control-Request-Headers")
        if requested_headers:
            if "*" in self.allow_headers:
                response.headers["Access-Control-Allow-Headers"] = requested_headers
            else:
                # Filter requested headers against allowed headers
                allowed = [h for h in requested_headers.split(", ") if h in self.allow_headers]
                if allowed:
                    response.headers["Access-Control-Allow-Headers"] = ", ".join(allowed)
        elif self.allow_headers and "*" not in self.allow_headers:
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        
        logger.debug(f"Handled OPTIONS request for {request.url} with 200 OK")
        return response
    
    def _add_cors_headers(self, response: Response, request: Request):
        """
        Add CORS headers to the response.
        """
        origin = request.headers.get("Origin")
        
        # Handle origin
        if origin and (origin in self.allow_origins or "*" in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allow_origins and not self.allow_credentials:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        # Add credentials header if needed
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Add expose headers
        if self.expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
        
        # Add vary header for proper caching
        response.headers["Vary"] = "Origin"