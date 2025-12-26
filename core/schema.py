from pydantic import BaseModel
from typing import Optional, List, Dict

class TestResult(BaseModel):
    provider: str
    model: str
    success: bool
    ttft_ms: float = 0.0  # Time to First Token
    total_latency_ms: float = 0.0
    output_tokens: int = 0
    tps: float = 0.0 # Tokens Per Second
    error_message: Optional[str] = None
    response_content: Optional[str] = None
    reasoning_content: Optional[str] = None # Chain of thought content
    
    # New fields for capabilities
    category: Optional[str] = "General"
    score: float = 0.0 # 0-100 score for this specific test
    evaluation_reason: Optional[str] = None
    case_name: Optional[str] = None
    case_type: Optional[str] = None
    details: Dict = {}  # Flexible dict for experiment-specific metrics

class ChatMessage(BaseModel):
    role: str
    content: str
