"""Job data models."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime


class JobData(BaseModel):
    """Structured job posting data."""
    
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Full job description")
    requirements: List[str] = Field(default_factory=list, description="Required qualifications")
    nice_to_have: List[str] = Field(default_factory=list, description="Preferred qualifications")
    salary: Optional[str] = Field(None, description="Salary range")
    url: str = Field(..., description="Job posting URL")
    scraped_at: datetime = Field(default_factory=datetime.now, description="Scrape timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "location": "London, UK",
                "description": "We are looking for...",
                "requirements": ["5+ years experience", "Python", "AWS"],
                "nice_to_have": ["Kubernetes", "Machine Learning"],
                "salary": "£70,000 - £90,000",
                "url": "https://example.com/jobs/123",
            }
        }
