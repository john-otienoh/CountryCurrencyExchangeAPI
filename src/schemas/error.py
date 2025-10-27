from pydantic import BaseModel
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str
    details: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response"""

    error: str = "Validation failed"
    details: Dict[str, str]


class NotFoundError(BaseModel):
    """404 error response"""

    error: str = "Country not found"


class ServiceUnavailableError(BaseModel):
    """503 error response for external API failures"""

    error: str = "External data source unavailable"
    details: str
