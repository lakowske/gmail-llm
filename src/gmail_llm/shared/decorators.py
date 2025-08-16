"""
Shared decorators for Gmail LLM application.
Eliminates code duplication in error handling and logging.
"""

import logging
import functools
import uuid
from datetime import datetime
from typing import Dict, Any, Callable, Optional

from .gmail_factory import get_gmail_connector

logger = logging.getLogger(__name__)


def gmail_operation(operation_name: str, 
                   include_connector: bool = True,
                   log_result: bool = True):
    """
    Decorator for Gmail operations that provides:
    - Automatic Gmail connector injection
    - Standardized error handling
    - Consistent logging
    - Operation correlation IDs
    
    Args:
        operation_name: Name of the operation for logging
        include_connector: If True, inject connector as first argument
        log_result: If True, log successful operation results
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            correlation_id = str(uuid.uuid4())[:8]
            start_time = datetime.utcnow()
            
            logger.info(f"{operation_name} started", extra={
                "operation": operation_name,
                "correlation_id": correlation_id,
                "timestamp": start_time.isoformat()
            })
            
            try:
                # Inject Gmail connector if requested
                if include_connector:
                    connector = get_gmail_connector()
                    result = func(connector, *args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Log successful completion
                if log_result:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    logger.info(f"{operation_name} completed successfully", extra={
                        "operation": operation_name,
                        "correlation_id": correlation_id,
                        "duration_seconds": duration,
                        "success": True
                    })
                
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                error_msg = f"Error in {operation_name}: {str(e)}"
                
                logger.error(error_msg, extra={
                    "operation": operation_name,
                    "correlation_id": correlation_id,
                    "duration_seconds": duration,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                
                return {
                    "success": False,
                    "message": error_msg,
                    "operation": operation_name,
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__
                }
        
        return wrapper
    return decorator


def http_operation(operation_name: str):
    """
    Decorator for HTTP API operations that provides:
    - Request correlation IDs
    - Performance logging
    - Standardized error responses
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            correlation_id = str(uuid.uuid4())[:8]
            start_time = datetime.utcnow()
            
            logger.info(f"HTTP {operation_name} started", extra={
                "operation": operation_name,
                "correlation_id": correlation_id,
                "timestamp": start_time.isoformat(),
                "type": "http_request"
            })
            
            try:
                result = await func(*args, **kwargs)
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"HTTP {operation_name} completed", extra={
                    "operation": operation_name,
                    "correlation_id": correlation_id,
                    "duration_seconds": duration,
                    "success": True,
                    "type": "http_response"
                })
                
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.error(f"HTTP {operation_name} failed", extra={
                    "operation": operation_name,
                    "correlation_id": correlation_id,
                    "duration_seconds": duration,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "type": "http_error"
                })
                raise
        
        return wrapper
    return decorator


def retry_on_auth_failure(max_retries: int = 1):
    """
    Decorator that retries Gmail operations on authentication failures.
    
    Args:
        max_retries: Maximum number of retry attempts
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is an auth-related error that we should retry
                    if (attempt < max_retries and 
                        ("authentication" in str(e).lower() or 
                         "unauthorized" in str(e).lower() or
                         "credentials" in str(e).lower())):
                        
                        logger.warning(f"Authentication failure on attempt {attempt + 1}, retrying...", extra={
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "error": str(e)
                        })
                        
                        # Reset the Gmail connector to force re-authentication
                        from .gmail_factory import reset_gmail_connector
                        reset_gmail_connector()
                        continue
                    else:
                        # Don't retry for non-auth errors or if max retries reached
                        break
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


def validate_message_ids(func: Callable) -> Callable:
    """
    Decorator that validates message IDs parameter and converts to list.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Find message_ids parameter
        if 'message_ids' in kwargs:
            message_ids = kwargs['message_ids']
            if isinstance(message_ids, str):
                id_list = [msg_id.strip() for msg_id in message_ids.split(",") if msg_id.strip()]
                if not id_list:
                    return {
                        "success": False,
                        "message": "No valid message IDs provided",
                        "total_messages": 0,
                        "successful_count": 0,
                        "failed_count": 0,
                        "results": []
                    }
                kwargs['message_ids'] = id_list
        
        return func(*args, **kwargs)
    return wrapper