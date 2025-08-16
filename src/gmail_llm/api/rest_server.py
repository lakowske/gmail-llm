"""
FastAPI REST server that wraps the existing MCP Gmail functionality.
Provides HTTP endpoints for other services to access Gmail operations.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from ..shared.gmail_factory import get_gmail_connector
from ..shared.decorators import gmail_operation
from ..shared.utils import validate_max_results, format_email_info, parse_label_list

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Gmail LLM API",
    description="HTTP API for Gmail operations, direct Gmail connector access",
    version="1.0.0"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class EmailReadRequest(BaseModel):
    query: str = Field(default="", description="Gmail search query")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of emails to retrieve")

class EmailSendRequest(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    message: str = Field(..., description="Plain text email content")
    html_content: Optional[str] = Field(None, description="Optional HTML email content")

class EmailActionRequest(BaseModel):
    message_id: str = Field(..., description="Gmail message ID")

class EmailLabelRequest(BaseModel):
    message_id: str = Field(..., description="Gmail message ID")
    add_labels: str = Field(default="", description="Comma-separated list of label IDs to add")
    remove_labels: str = Field(default="", description="Comma-separated list of label IDs to remove")

class BulkEmailActionRequest(BaseModel):
    message_ids: str = Field(..., description="Comma-separated list of Gmail message IDs")

class BulkEmailLabelRequest(BaseModel):
    message_ids: str = Field(..., description="Comma-separated list of Gmail message IDs")
    add_labels: str = Field(default="", description="Comma-separated list of label IDs to add")
    remove_labels: str = Field(default="", description="Comma-separated list of label IDs to remove")

# Helper function to get Gmail connector
def get_connector():
    """Get Gmail connector instance."""
    return get_gmail_connector()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "gmail-llm-api"}

# Email reading endpoints
@app.get("/api/emails")
async def read_emails(
    query: str = "",
    max_results: int = 10,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """
    Read emails from Gmail inbox with optional search query.
    
    Args:
        query: Gmail search query (e.g., 'is:unread', 'from:user@example.com')
        max_results: Maximum number of emails to retrieve (1-50)
    
    Returns:
        Dictionary containing success status, message, emails list, and count
    """
    try:
        # Validate max_results
        max_results = validate_max_results(max_results)
        
        # Read emails
        raw_emails = connector.get_messages(query=query, max_results=max_results)
        
        if not raw_emails:
            return {
                "success": True,
                "message": "No emails found",
                "emails": [],
                "count": 0
            }
        
        # Format emails
        formatted_emails = []
        for raw_email in raw_emails:
            formatted_email = format_email_info(raw_email, connector)
            formatted_emails.append(formatted_email)
        
        return {
            "success": True,
            "message": f"Retrieved {len(formatted_emails)} emails",
            "emails": formatted_emails,
            "count": len(formatted_emails)
        }
        
    except Exception as e:
        logger.error(f"Error in read_emails endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/read")
async def read_emails_post(
    request: EmailReadRequest,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """
    Read emails from Gmail inbox with optional search query (POST version).
    """
    try:
        # Use the same logic as the GET endpoint
        max_results = validate_max_results(request.max_results)
        raw_emails = connector.get_messages(query=request.query, max_results=max_results)
        
        if not raw_emails:
            return {
                "success": True,
                "message": "No emails found", 
                "emails": [],
                "count": 0
            }
        
        formatted_emails = []
        for raw_email in raw_emails:
            formatted_email = format_email_info(raw_email, connector)
            formatted_emails.append(formatted_email)
        
        return {
            "success": True,
            "message": f"Retrieved {len(formatted_emails)} emails",
            "emails": formatted_emails,
            "count": len(formatted_emails)
        }
    except Exception as e:
        logger.error(f"Error in read_emails_post endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Email sending endpoint
@app.post("/api/emails/send")
async def send_email(
    request: EmailSendRequest,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """
    Send an email via Gmail.
    """
    try:
        # Send email using connector
        success = connector.send_email(
            to=request.to,
            subject=request.subject, 
            message_text=request.message,
            html_content=request.html_content
        )
        
        if success:
            return {
                "success": True,
                "message": f"Email sent successfully to {request.to}",
                "message_id": None
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to send email")
            
    except Exception as e:
        logger.error(f"Error in send_email endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Email action endpoints
@app.post("/api/emails/{message_id}/mark-read")
async def mark_email_as_read(
    message_id: str,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Mark an email as read by removing the UNREAD label."""
    try:
        result = connector.mark_as_read(message_id=message_id)
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to mark email as read"))
        return result
    except Exception as e:
        logger.error(f"Error in mark_email_as_read endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{message_id}/mark-spam")
async def mark_email_as_spam(
    message_id: str,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Mark an email as spam by moving it to the spam folder."""
    try:
        result = connector.mark_as_spam(message_id=message_id)
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to mark email as spam"))
        return result
    except Exception as e:
        logger.error(f"Error in mark_email_as_spam endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{message_id}/trash")
async def move_email_to_trash(
    message_id: str,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Move an email to trash."""
    try:
        result = connector.move_to_trash(message_id=message_id)
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to move email to trash"))
        return result
    except Exception as e:
        logger.error(f"Error in move_email_to_trash endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{message_id}/star")
async def add_star_to_email(
    message_id: str,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Add a star to an email."""
    try:
        result = connector.add_star(message_id=message_id)
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to add star to email"))
        return result
    except Exception as e:
        logger.error(f"Error in add_star_to_email endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{message_id}/labels")
async def modify_email_labels(
    message_id: str,
    request: EmailLabelRequest,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Modify labels on an email by adding or removing specific labels."""
    try:
        result = connector.modify_labels(
            message_id=message_id,
            add_labels=request.add_labels,
            remove_labels=request.remove_labels
        )
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to modify email labels"))
        return result
    except Exception as e:
        logger.error(f"Error in modify_email_labels endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Bulk operation endpoints
@app.post("/api/emails/bulk/mark-read")
async def bulk_mark_emails_as_read(
    request: BulkEmailActionRequest,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Mark multiple emails as read by removing the UNREAD label."""
    try:
        result = connector.bulk_mark_as_read(message_ids=request.message_ids)
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to bulk mark emails as read"))
        return result
    except Exception as e:
        logger.error(f"Error in bulk_mark_emails_as_read endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/bulk/mark-spam")
async def bulk_mark_emails_as_spam(
    request: BulkEmailActionRequest,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Mark multiple emails as spam by moving them to the spam folder."""
    try:
        result = connector.bulk_mark_as_spam(message_ids=request.message_ids)
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to bulk mark emails as spam"))
        return result
    except Exception as e:
        logger.error(f"Error in bulk_mark_emails_as_spam endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/bulk/trash")
async def bulk_move_emails_to_trash(
    request: BulkEmailActionRequest,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Move multiple emails to trash."""
    try:
        result = connector.bulk_move_to_trash(message_ids=request.message_ids)
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to bulk move emails to trash"))
        return result
    except Exception as e:
        logger.error(f"Error in bulk_move_emails_to_trash endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/bulk/star")
async def bulk_add_stars_to_emails(
    request: BulkEmailActionRequest,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Add star to multiple emails."""
    try:
        result = connector.bulk_add_star(message_ids=request.message_ids)
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to bulk add stars to emails"))
        return result
    except Exception as e:
        logger.error(f"Error in bulk_add_stars_to_emails endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/bulk/labels")
async def bulk_modify_email_labels(
    request: BulkEmailLabelRequest,
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Modify labels on multiple emails by adding or removing specific labels."""
    try:
        result = connector.bulk_modify_labels(
            message_ids=request.message_ids,
            add_labels=request.add_labels,
            remove_labels=request.remove_labels
        )
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to bulk modify email labels"))
        return result
    except Exception as e:
        logger.error(f"Error in bulk_modify_email_labels endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Labels endpoint
@app.get("/api/labels")
async def get_available_labels(
    connector = Depends(get_connector)
) -> Dict[str, Any]:
    """Get list of available labels in the Gmail account."""
    try:
        result = connector.get_available_labels()
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to get available labels"))
        return result
    except Exception as e:
        logger.error(f"Error in get_available_labels endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_server(host: str = "127.0.0.1", port: int = 8000, log_level: str = "info"):
    """Run the FastAPI server."""
    uvicorn.run(app, host=host, port=port, log_level=log_level)

if __name__ == "__main__":
    run_server()