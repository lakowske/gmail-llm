"""
Structured logging configuration for Gmail LLM application.
Provides consistent logging format and correlation tracking.
"""

import logging
import logging.config
import sys
from typing import Dict, Any
import json
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs with correlation support.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields from record
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                              'relativeCreated', 'thread', 'threadName', 'processName', 
                              'process', 'stack_info', 'exc_info', 'exc_text', 'getMessage']:
                    log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add stack info if present
        if record.stack_info:
            log_data["stack_info"] = record.stack_info
            
        return json.dumps(log_data, default=str)


def setup_logging(log_level: str = "info", 
                 structured: bool = True,
                 correlation_enabled: bool = True) -> None:
    """
    Setup application logging configuration.
    
    Args:
        log_level: Logging level (debug, info, warning, error)
        structured: Whether to use structured JSON logging
        correlation_enabled: Whether to enable correlation ID tracking
    """
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    if structured:
        # Structured JSON logging configuration
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structured": {
                    "()": StructuredFormatter,
                },
                "simple": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level.upper(),
                    "formatter": "structured" if structured else "simple",
                    "stream": "ext://sys.stdout"
                }
            },
            "loggers": {
                "gmail_llm": {
                    "level": log_level.upper(),
                    "handlers": ["console"],
                    "propagate": False
                },
                "fastmcp": {
                    "level": "WARNING",  # Reduce noise from FastMCP
                    "handlers": ["console"],
                    "propagate": False
                },
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False
                }
            },
            "root": {
                "level": log_level.upper(),
                "handlers": ["console"]
            }
        }
    else:
        # Simple console logging for development
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level.upper(),
                    "formatter": "simple",
                    "stream": "ext://sys.stdout"
                }
            },
            "root": {
                "level": log_level.upper(),
                "handlers": ["console"]
            }
        }
    
    logging.config.dictConfig(config)
    
    # Add correlation tracking if enabled
    if correlation_enabled:
        setup_correlation_tracking()


def setup_correlation_tracking():
    """Setup correlation ID tracking for request tracing."""
    
    # Add custom log adapter for correlation
    class CorrelationAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            # Add correlation ID from context if available
            if hasattr(self.extra, 'correlation_id'):
                return f"[{self.extra['correlation_id']}] {msg}", kwargs
            return msg, kwargs
    
    # This would be enhanced with actual correlation context management
    # For now, it's a placeholder for future implementation


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with proper configuration.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_performance(operation: str, duration: float, **extra_data):
    """
    Log performance metrics for operations.
    
    Args:
        operation: Name of the operation
        duration: Duration in seconds
        **extra_data: Additional metrics to log
    """
    logger = get_logger("gmail_llm.performance")
    logger.info("Performance metric", extra={
        "metric_type": "performance",
        "operation": operation,
        "duration_seconds": duration,
        **extra_data
    })


def log_business_event(event: str, **event_data):
    """
    Log business events for monitoring and analytics.
    
    Args:
        event: Event name
        **event_data: Event-specific data
    """
    logger = get_logger("gmail_llm.business")
    logger.info("Business event", extra={
        "event_type": "business",
        "event": event,
        **event_data
    })


def log_security_event(event: str, severity: str = "info", **event_data):
    """
    Log security-related events.
    
    Args:
        event: Security event name
        severity: Event severity (info, warning, error, critical)
        **event_data: Event-specific data
    """
    logger = get_logger("gmail_llm.security")
    log_method = getattr(logger, severity.lower(), logger.info)
    log_method("Security event", extra={
        "event_type": "security",
        "event": event,
        "severity": severity,
        **event_data
    })