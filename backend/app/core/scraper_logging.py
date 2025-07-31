"""
Enhanced logging and error handling system for scraping operations.
Provides structured logging, error tracking, and performance monitoring.
"""

from __future__ import annotations

import logging
import traceback
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager


# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraping.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorType(Enum):
    """Error type classification."""
    NETWORK_ERROR = "network_error"
    PARSING_ERROR = "parsing_error"
    DATABASE_ERROR = "database_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    PERMISSION_ERROR = "permission_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ScrapingError:
    """Structured error information."""
    error_type: ErrorType
    message: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    traceback: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    is_recoverable: bool = True


@dataclass
class ScrapingMetrics:
    """Performance and operational metrics."""
    source: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: float = 0.0
    events_scraped: int = 0
    events_saved: int = 0
    pages_processed: int = 0
    errors: List[ScrapingError] = field(default_factory=list)
    success_rate: float = 0.0
    memory_usage: Optional[float] = None
    
    def complete(self) -> None:
        """Mark metrics as completed and calculate final values."""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        if self.events_scraped > 0:
            self.success_rate = (self.events_saved / self.events_scraped) * 100
    
    def add_error(self, error: ScrapingError) -> None:
        """Add an error to the metrics."""
        self.errors.append(error)
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get error summary by type."""
        summary = {}
        for error in self.errors:
            error_type = error.error_type.value
            summary[error_type] = summary.get(error_type, 0) + 1
        return summary


class ScrapingLogger:
    """Enhanced logging system for scraping operations."""
    
    def __init__(self, source: str):
        self.source = source
        self.logger = logging.getLogger(f"scraping.{source}")
        self.metrics = ScrapingMetrics(source=source)
        self.errors: List[ScrapingError] = []
        
    def log_start(self, max_pages: int, **kwargs) -> None:
        """Log scraping start."""
        self.logger.info(
            f"Starting scraping for {self.source} - max_pages: {max_pages}, "
            f"params: {kwargs}"
        )
        
    def log_page_start(self, page_num: int, url: str) -> None:
        """Log page scraping start."""
        self.logger.debug(f"Scraping page {page_num}: {url}")
        
    def log_page_complete(self, page_num: int, events_found: int) -> None:
        """Log page scraping completion."""
        self.logger.debug(f"Page {page_num} completed - {events_found} events found")
        self.metrics.pages_processed += 1
        self.metrics.events_scraped += events_found
        
    def log_event_saved(self, event_title: str) -> None:
        """Log successful event save."""
        self.logger.debug(f"Event saved: {event_title}")
        self.metrics.events_saved += 1
        
    def log_event_skipped(self, event_title: str, reason: str) -> None:
        """Log skipped event."""
        self.logger.debug(f"Event skipped: {event_title} - {reason}")
        
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> ScrapingError:
        """Log and track an error."""
        error_type = self._classify_error(error)
        scraping_error = ScrapingError(
            error_type=error_type,
            message=str(error),
            source=self.source,
            traceback=traceback.format_exc(),
            context=context or {},
            is_recoverable=self._is_recoverable(error_type)
        )
        
        self.errors.append(scraping_error)
        self.metrics.add_error(scraping_error)
        
        # Log with appropriate level
        if error_type in [ErrorType.NETWORK_ERROR, ErrorType.TIMEOUT_ERROR]:
            self.logger.warning(f"Recoverable error in {self.source}: {error}")
        else:
            self.logger.error(f"Error in {self.source}: {error}")
            
        return scraping_error
        
    def log_retry(self, error: ScrapingError, attempt: int, max_attempts: int) -> None:
        """Log retry attempt."""
        error.retry_count = attempt
        self.logger.info(
            f"Retry {attempt}/{max_attempts} for {self.source} - "
            f"Error: {error.message}"
        )
        
    def log_completion(self, success: bool = True) -> None:
        """Log scraping completion."""
        self.metrics.complete()
        
        if success:
            self.logger.info(
                f"Scraping completed for {self.source} - "
                f"Duration: {self.metrics.duration:.2f}s, "
                f"Events: {self.metrics.events_scraped} scraped, "
                f"{self.metrics.events_saved} saved, "
                f"Success rate: {self.metrics.success_rate:.1f}%"
            )
        else:
            self.logger.error(
                f"Scraping failed for {self.source} - "
                f"Duration: {self.metrics.duration:.2f}s, "
                f"Errors: {len(self.errors)}"
            )
            
    def get_metrics(self) -> ScrapingMetrics:
        """Get current metrics."""
        return self.metrics
        
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary."""
        if not self.errors:
            return {"total_errors": 0, "error_types": {}}
            
        return {
            "total_errors": len(self.errors),
            "error_types": self.metrics.get_error_summary(),
            "recoverable_errors": len([e for e in self.errors if e.is_recoverable]),
            "critical_errors": len([e for e in self.errors if not e.is_recoverable])
        }
        
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type."""
        error_str = str(error).lower()
        
        if any(keyword in error_str for keyword in ["network", "connection", "dns", "host"]):
            return ErrorType.NETWORK_ERROR
        elif any(keyword in error_str for keyword in ["timeout", "read timeout"]):
            return ErrorType.TIMEOUT_ERROR
        elif any(keyword in error_str for keyword in ["parse", "parsing", "invalid html"]):
            return ErrorType.PARSING_ERROR
        elif any(keyword in error_str for keyword in ["database", "sql", "constraint"]):
            return ErrorType.DATABASE_ERROR
        elif any(keyword in error_str for keyword in ["validation", "invalid"]):
            return ErrorType.VALIDATION_ERROR
        elif any(keyword in error_str for keyword in ["permission", "forbidden", "unauthorized"]):
            return ErrorType.PERMISSION_ERROR
        elif any(keyword in error_str for keyword in ["config", "configuration", "setting"]):
            return ErrorType.CONFIGURATION_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
            
    def _is_recoverable(self, error_type: ErrorType) -> bool:
        """Determine if error is recoverable."""
        recoverable_errors = [
            ErrorType.NETWORK_ERROR,
            ErrorType.TIMEOUT_ERROR,
            ErrorType.PARSING_ERROR  # Sometimes recoverable
        ]
        return error_type in recoverable_errors


class ScrapingLoggerManager:
    """Manager for scraping loggers."""
    
    def __init__(self):
        self.active_loggers: Dict[str, ScrapingLogger] = {}
        
    def get_logger(self, source: str) -> ScrapingLogger:
        """Get or create logger for source."""
        if source not in self.active_loggers:
            self.active_loggers[source] = ScrapingLogger(source)
        return self.active_loggers[source]
        
    def remove_logger(self, source: str) -> None:
        """Remove logger for source."""
        if source in self.active_loggers:
            del self.active_loggers[source]
            
    def get_all_metrics(self) -> Dict[str, ScrapingMetrics]:
        """Get metrics for all active loggers."""
        return {
            source: logger.get_metrics() 
            for source, logger in self.active_loggers.items()
        }
        
    def get_global_summary(self) -> Dict[str, Any]:
        """Get global scraping summary."""
        total_scraped = sum(
            logger.metrics.events_scraped 
            for logger in self.active_loggers.values()
        )
        total_saved = sum(
            logger.metrics.events_saved 
            for logger in self.active_loggers.values()
        )
        total_errors = sum(
            len(logger.errors) 
            for logger in self.active_loggers.values()
        )
        
        return {
            "active_scrapers": len(self.active_loggers),
            "total_events_scraped": total_scraped,
            "total_events_saved": total_saved,
            "total_errors": total_errors,
            "global_success_rate": (total_saved / total_scraped * 100) if total_scraped > 0 else 0
        }


@asynccontextmanager
async def scraping_context(source: str, max_pages: int = 5, **kwargs):
    """Context manager for scraping operations with automatic logging."""
    logger_manager = get_scraping_logger_manager()
    scraping_logger = logger_manager.get_logger(source)
    
    try:
        scraping_logger.log_start(max_pages, **kwargs)
        yield scraping_logger
        scraping_logger.log_completion(success=True)
    except Exception as e:
        scraping_logger.log_error(e)
        scraping_logger.log_completion(success=False)
        raise
    finally:
        # Clean up logger after some time to prevent memory leaks
        # In a real implementation, you might want to keep recent logs for monitoring
        pass


# Global logger manager instance
_logger_manager = ScrapingLoggerManager()


def get_scraping_logger_manager() -> ScrapingLoggerManager:
    """Get global scraping logger manager."""
    return _logger_manager


def get_scraping_logger(source: str) -> ScrapingLogger:
    """Get scraping logger for source."""
    return _logger_manager.get_logger(source)