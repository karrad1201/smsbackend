from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class Provider(BaseModel):
    id: int
    name: str
    adapter_class: str
    config: Dict[str, Any]
    is_active: bool = True
    display_name: Optional[str] = None
    api_url: Optional[str] = None
    priority: int = 100
    max_requests_per_second: int = 10
    timeout_seconds: int = 20
    adapter_type: str = 'smslive'
    mapping_type: str = 'smsactivate_type'
    max_requests_per_minute: int = 250
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProviderCreate(BaseModel):
    name: str
    adapter_class: str
    config: Dict[str, Any]
    display_name: Optional[str] = None
    api_url: Optional[str] = None
    priority: int = 100