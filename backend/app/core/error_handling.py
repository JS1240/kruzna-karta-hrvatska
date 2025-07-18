"""
Comprehensive error handling system for scraping operations.
Provides error recovery, retry mechanisms, and proper error reporting.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import time

from .scraper_logging import get_scraping_logger, ErrorType, ScrapingError

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy enumeration."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE = "immediate"


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    backoff_factor: float = 2.0
    jitter: bool = True
    retry_exceptions: List[Type[Exception]] = None
    
    def __post_init__(self):
        if self.retry_exceptions is None:
            # Default exceptions that should trigger retries
            self.retry_exceptions = [
                ConnectionError,
                TimeoutError,
                OSError,
                asyncio.TimeoutError,
            ]


class CircuitBreakerState(Enum):
    """Circuit breaker state enumeration."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 3  # Successes needed to close from half-open
    
    
class CircuitBreaker:
    """Circuit breaker implementation for scraping operations."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        
    def should_allow_request(self) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        else:  # HALF_OPEN
            return True
            
    def record_success(self) -> None:
        """Record successful request."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
            
    def record_failure(self) -> None:
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            
    def get_state(self) -> CircuitBreakerState:
        """Get current state."""
        return self.state


class ErrorHandler:
    """Comprehensive error handling for scraping operations."""
    
    def __init__(self, source: str):
        self.source = source
        self.logger = get_scraping_logger(source)
        self.circuit_breaker = CircuitBreaker(CircuitBreakerConfig())
        self.retry_configs: Dict[str, RetryConfig] = {}
        
    def add_retry_config(self, operation: str, config: RetryConfig) -> None:
        """Add retry configuration for specific operation."""
        self.retry_configs[operation] = config
        
    def get_retry_config(self, operation: str) -> RetryConfig:
        """Get retry configuration for operation."""
        return self.retry_configs.get(operation, RetryConfig())
        
    async def execute_with_retry(
        self,
        operation: Callable,
        operation_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with retry logic."""
        config = self.get_retry_config(operation_name)
        
        # Check circuit breaker
        if not self.circuit_breaker.should_allow_request():
            raise RuntimeError(f"Circuit breaker open for {self.source}")
            
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                result = await operation(*args, **kwargs)
                
                # Record success
                self.circuit_breaker.record_success()
                
                if attempt > 0:
                    self.logger.logger.info(
                        f"Operation {operation_name} succeeded on attempt {attempt + 1}"
                    )
                    
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if this exception should trigger retry
                if not self._should_retry(e, config):
                    self.circuit_breaker.record_failure()
                    raise
                    
                # Log error
                scraping_error = self.logger.log_error(e, {
                    "operation": operation_name,
                    "attempt": attempt + 1,
                    "max_attempts": config.max_attempts
                })
                
                # Don't retry on last attempt
                if attempt == config.max_attempts - 1:
                    self.circuit_breaker.record_failure()
                    break
                    
                # Calculate delay
                delay = self._calculate_delay(attempt, config)
                
                # Log retry
                self.logger.log_retry(scraping_error, attempt + 1, config.max_attempts)
                
                # Wait before retry
                await asyncio.sleep(delay)
                
        # All attempts failed
        self.circuit_breaker.record_failure()
        raise last_exception
        
    def _should_retry(self, exception: Exception, config: RetryConfig) -> bool:
        """Check if exception should trigger retry."""
        return any(isinstance(exception, exc_type) for exc_type in config.retry_exceptions)
        
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt."""
        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_factor ** attempt)
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)
        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
        else:  # IMMEDIATE
            delay = 0
            
        # Apply jitter if enabled
        if config.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
            
        # Ensure delay doesn't exceed max_delay
        return min(delay, config.max_delay)
        
    async def handle_network_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Handle network-related errors."""
        self.logger.log_error(error, context)
        
        # Could implement additional network error handling here
        # such as switching to backup proxies, etc.
        
    async def handle_parsing_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Handle parsing-related errors."""
        self.logger.log_error(error, context)
        
        # Could implement fallback parsing strategies
        
    async def handle_database_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Handle database-related errors."""
        self.logger.log_error(error, context)
        
        # Could implement database connection recovery
        
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "circuit_breaker_state": self.circuit_breaker.get_state().value,
            "total_errors": len(self.logger.errors),
            "error_summary": self.logger.get_error_summary(),
            "failure_count": self.circuit_breaker.failure_count
        }


def with_error_handling(
    source: str,
    operation_name: str,
    retry_config: Optional[RetryConfig] = None
):
    """Decorator for adding error handling to scraping operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            error_handler = ErrorHandler(source)
            
            if retry_config:
                error_handler.add_retry_config(operation_name, retry_config)
                
            return await error_handler.execute_with_retry(
                func, operation_name, *args, **kwargs
            )
            
        return wrapper
    return decorator


class ScrapingErrorManager:
    """Global error manager for scraping operations."""
    
    def __init__(self):
        self.error_handlers: Dict[str, ErrorHandler] = {}
        self.global_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "retry_attempts": 0
        }
        
    def get_error_handler(self, source: str) -> ErrorHandler:
        """Get error handler for source."""
        if source not in self.error_handlers:
            self.error_handlers[source] = ErrorHandler(source)
        return self.error_handlers[source]
        
    def record_operation(self, success: bool, retry_count: int = 0) -> None:
        """Record operation statistics."""
        self.global_stats["total_operations"] += 1
        if success:
            self.global_stats["successful_operations"] += 1
        else:
            self.global_stats["failed_operations"] += 1
        self.global_stats["retry_attempts"] += retry_count
        
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global error statistics."""
        total_ops = self.global_stats["total_operations"]
        success_rate = (
            self.global_stats["successful_operations"] / total_ops * 100 
            if total_ops > 0 else 0
        )
        
        return {
            **self.global_stats,
            "success_rate": success_rate,
            "active_handlers": len(self.error_handlers),
            "handlers_by_source": {
                source: handler.get_error_stats()
                for source, handler in self.error_handlers.items()
            }
        }
        
    def reset_stats(self) -> None:
        """Reset global statistics."""
        self.global_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "retry_attempts": 0
        }


# Global error manager instance
_error_manager = ScrapingErrorManager()


def get_error_manager() -> ScrapingErrorManager:
    """Get global error manager."""
    return _error_manager


def get_error_handler(source: str) -> ErrorHandler:
    """Get error handler for source."""
    return _error_manager.get_error_handler(source)


# Predefined retry configurations for common operations
RETRY_CONFIGS = {
    "fetch_page": RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retry_exceptions=[ConnectionError, TimeoutError, OSError]
    ),
    "parse_events": RetryConfig(
        max_attempts=2,
        base_delay=0.5,
        strategy=RetryStrategy.FIXED_DELAY,
        retry_exceptions=[AttributeError, ValueError]
    ),
    "save_to_database": RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        retry_exceptions=[ConnectionError, TimeoutError]
    )
}