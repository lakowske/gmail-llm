"""
Shared utility functions for Gmail LLM application.
Eliminates code duplication for common operations.
"""

import logging
from typing import List, Dict, Any, Optional
from ..config import get_config

logger = logging.getLogger(__name__)


def parse_message_ids(message_ids: str) -> List[str]:
    """
    Parse comma-separated message IDs and validate.
    
    Args:
        message_ids: Comma-separated string of message IDs
        
    Returns:
        List of cleaned message IDs
        
    Raises:
        ValueError: If no valid message IDs provided
    """
    if not message_ids or not isinstance(message_ids, str):
        raise ValueError("Message IDs must be a non-empty string")
    
    id_list = [msg_id.strip() for msg_id in message_ids.split(",") if msg_id.strip()]
    
    if not id_list:
        raise ValueError("No valid message IDs provided")
    
    return id_list


def parse_label_list(labels: str) -> Optional[List[str]]:
    """
    Parse comma-separated label IDs.
    
    Args:
        labels: Comma-separated string of label IDs
        
    Returns:
        List of cleaned label IDs, or None if empty
    """
    if not labels or not isinstance(labels, str):
        return None
    
    label_list = [label.strip() for label in labels.split(",") if label.strip()]
    return label_list if label_list else None


def validate_max_results(max_results: int) -> int:
    """
    Validate and clamp max_results parameter.
    
    Args:
        max_results: Requested maximum results
        
    Returns:
        Validated max_results value
        
    Raises:
        ValueError: If max_results is invalid
    """
    config = get_config()
    
    if not isinstance(max_results, int):
        raise ValueError("max_results must be an integer")
    
    if max_results < 1:
        raise ValueError("max_results must be at least 1")
    
    if max_results > config.gmail.max_results_limit:
        raise ValueError(f"max_results cannot exceed {config.gmail.max_results_limit}")
    
    return max_results


def format_email_info(raw_email: Dict[str, Any], connector) -> Dict[str, Any]:
    """
    Format raw email data into standardized format.
    
    Args:
        raw_email: Raw email data from Gmail API
        connector: Gmail connector instance for parsing
        
    Returns:
        Formatted email information dictionary
    """
    try:
        email_info = connector.extract_message_info(raw_email)
        return {
            "id": email_info.get("id", ""),
            "thread_id": email_info.get("thread_id", ""),
            "from": email_info.get("from", "Unknown"),
            "to": email_info.get("to", "Unknown"), 
            "subject": email_info.get("subject", "No Subject"),
            "date": email_info.get("date", "Unknown"),
            "snippet": email_info.get("snippet", ""),
            "label_ids": email_info.get("label_ids", [])
        }
    except Exception as e:
        logger.warning(f"Failed to format email info: {e}")
        return {
            "id": raw_email.get("id", ""),
            "thread_id": raw_email.get("threadId", ""),
            "from": "Unknown",
            "to": "Unknown",
            "subject": "Failed to parse",
            "date": "Unknown",
            "snippet": "Failed to parse email content",
            "label_ids": []
        }


def create_bulk_operation_result(operation_name: str, 
                               message_ids: List[str], 
                               results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create standardized bulk operation result.
    
    Args:
        operation_name: Name of the bulk operation
        message_ids: List of message IDs that were processed
        results: List of individual operation results
        
    Returns:
        Standardized bulk operation result
    """
    successful_count = sum(1 for result in results if result.get("success", False))
    failed_count = len(results) - successful_count
    
    return {
        "success": failed_count == 0,
        "message": f"Bulk {operation_name}: {successful_count}/{len(message_ids)} successful",
        "total_messages": len(message_ids),
        "successful_count": successful_count,
        "failed_count": failed_count,
        "results": results
    }


def sanitize_email_content(content: str, max_length: int = 1000) -> str:
    """
    Sanitize email content for logging (remove sensitive info, truncate).
    
    Args:
        content: Email content to sanitize
        max_length: Maximum length to keep
        
    Returns:
        Sanitized content string
    """
    if not content:
        return ""
    
    # Truncate if too long
    if len(content) > max_length:
        content = content[:max_length] + "..."
    
    # Could add more sanitization rules here (e.g., remove email addresses, phone numbers)
    return content


def validate_email_address(email: str) -> bool:
    """
    Basic email address validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email appears valid
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic validation - contains @ and has parts before and after
    parts = email.split("@")
    return len(parts) == 2 and len(parts[0]) > 0 and len(parts[1]) > 0 and "." in parts[1]


def create_success_response(message: str, **extra_data) -> Dict[str, Any]:
    """
    Create standardized success response.
    
    Args:
        message: Success message
        **extra_data: Additional data to include in response
        
    Returns:
        Standardized success response
    """
    response = {
        "success": True,
        "message": message
    }
    response.update(extra_data)
    return response


def create_error_response(message: str, 
                         operation: str = None, 
                         error_type: str = None,
                         **extra_data) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        message: Error message
        operation: Operation that failed
        error_type: Type of error
        **extra_data: Additional data to include in response
        
    Returns:
        Standardized error response
    """
    response = {
        "success": False,
        "message": message
    }
    
    if operation:
        response["operation"] = operation
    if error_type:
        response["error_type"] = error_type
    
    response.update(extra_data)
    return response