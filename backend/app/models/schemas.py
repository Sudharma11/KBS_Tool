from pydantic import BaseModel
from typing import Optional


class ComparisonRequest(BaseModel):
    company1_name: str
    company2_name: str
    company1_website: str
    company2_website: str
    company1_linkedin: str
    company2_linkedin: str
    use_predefined_data: bool = False
    # Optional: override the server-side LLM key/model per request
    api_key: Optional[str] = None
    model: Optional[str] = None
