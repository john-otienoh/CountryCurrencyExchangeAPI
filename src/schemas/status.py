from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class StatusResponse(BaseModel):
    """Schema for status endpoint response"""

    total_countries: int
    last_refreshed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
