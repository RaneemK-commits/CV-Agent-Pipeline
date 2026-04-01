"""Data schemas for storage."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime


class StoredCV(BaseModel):
    """Schema for stored CV data."""
    
    id: str = Field(..., description="Unique CV identifier")
    cv_data: Dict[str, Any] = Field(..., description="CV content")
    job_url: str = Field(..., description="Associated job URL")
    job_id: Optional[str] = Field(None, description="Associated job ID")
    scores: Dict[str, Any] = Field(default_factory=dict, description="Score report")
    html_content: Optional[str] = Field(None, description="Rendered HTML")
    pdf_path: Optional[str] = Field(None, description="Path to PDF file")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    iteration: int = Field(default=1, description="Refinement iteration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "cv_20240101_123456",
                "cv_data": {"personal_info": {}, "experience": []},
                "job_url": "https://example.com/jobs/123",
                "scores": {"ats": {"overall_score": 85}, "job_fit": {"overall_score": 78}},
                "pdf_path": "output/cvs/cv_20240101_123456.pdf",
            }
        }


class StoredJob(BaseModel):
    """Schema for stored job data."""
    
    id: str = Field(..., description="Unique job identifier")
    url: str = Field(..., description="Job posting URL")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    requirements: List[str] = Field(default_factory=list, description="Requirements")
    nice_to_have: List[str] = Field(default_factory=list, description="Nice to have")
    scraped_at: datetime = Field(default_factory=datetime.now, description="Scrape timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "job_20240101_123456",
                "url": "https://example.com/jobs/123",
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "description": "We are looking for...",
                "requirements": ["5+ years experience", "Python", "AWS"],
            }
        }


class PipelineRun(BaseModel):
    """Schema for pipeline run history."""
    
    id: str = Field(..., description="Unique run identifier")
    job_url: str = Field(..., description="Job posting URL")
    experience_file: str = Field(..., description="Path to experience file")
    started_at: datetime = Field(default_factory=datetime.now, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    status: str = Field(default="running", description="Run status")
    cv_id: Optional[str] = Field(None, description="Generated CV ID")
    final_scores: Optional[Dict[str, Any]] = Field(None, description="Final scores")
    iterations: int = Field(default=1, description="Number of refinement iterations")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "run_20240101_123456",
                "job_url": "https://example.com/jobs/123",
                "status": "completed",
                "cv_id": "cv_20240101_123456",
                "final_scores": {"ats": 85, "job_fit": 78},
                "iterations": 2,
            }
        }


class VectorSearchResult(BaseModel):
    """Schema for vector search results."""
    
    id: str = Field(..., description="Result ID")
    score: float = Field(..., description="Similarity score")
    data: Dict[str, Any] = Field(..., description="Result data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "cv_20240101_123456",
                "score": 0.92,
                "data": {"personal_info": {}, "experience": []},
                "metadata": {"ats_score": 85, "job_url": "https://example.com/jobs/123"},
            }
        }
