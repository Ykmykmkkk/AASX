# api/schemas.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class DslRequest(BaseModel):
    # Field의 ...은 필수 필드임을 의미합니다.
    goal: str = Field(..., example="query_failed_jobs_with_cooling")
    
    # 각 Goal에 따라 선택적으로 사용되는 파라미터들
    date: Optional[str] = Field(None, example="2025-07-17")
    product_id: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None
    target_machine: Optional[str] = None
    quantity: Optional[int] = None

class ApiResponse(BaseModel):
    goal: str
    params: Dict[str, Any]
    result: Any