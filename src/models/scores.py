"""Score report models."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class ATSScore(BaseModel):
    """ATS compatibility score details."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_score": 85,
                "checks": {
                    "contact_info_present": True,
                    "standard_headings": True,
                    "no_images_in_content": True,
                    "text_selectable": True,
                },
                "flags": [],
                "suggestions": ["Consider adding more keywords from job description"],
            }
        }
    )
    
    overall_score: int = Field(..., ge=0, le=100, description="Overall ATS score (0-100)")
    checks: Dict[str, bool] = Field(default_factory=dict, description="Individual check results")
    flags: List[str] = Field(default_factory=list, description="ATS compatibility issues")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class JobFitScore(BaseModel):
    """Job fit score details."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_score": 78,
                "skill_match_percentage": 75,
                "matched_skills": ["Python", "AWS", "Docker"],
                "missing_skills": ["Kubernetes"],
                "experience_alignment": "Strong match",
                "gaps": [],
                "strengths": [],
            }
        }
    )
    
    overall_score: int = Field(..., ge=0, le=100, description="Job fit score (0-100)")
    skill_match_percentage: int = Field(..., ge=0, le=100, description="Percentage of required skills matched")
    matched_skills: List[str] = Field(default_factory=list, description="Skills that match the job")
    missing_skills: List[str] = Field(default_factory=list, description="Required skills not found")
    experience_alignment: str = Field(..., description="Assessment of experience level match")
    gaps: List[str] = Field(default_factory=list, description="Identified gaps")
    strengths: List[str] = Field(default_factory=list, description="Key strengths for this role")


class ScoreReport(BaseModel):
    """Complete score report for a CV."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ats": {"overall_score": 85, "checks": {}, "flags": [], "suggestions": []},
                "job_fit": {
                    "overall_score": 78,
                    "skill_match_percentage": 75,
                    "matched_skills": [],
                    "missing_skills": [],
                    "experience_alignment": "Strong match",
                    "gaps": [],
                    "strengths": [],
                },
                "cv_version": 1,
                "job_url": "https://example.com/jobs/123",
                "meets_thresholds": True,
            }
        }
    )
    
    ats: ATSScore = Field(..., description="ATS compatibility score")
    job_fit: JobFitScore = Field(..., description="Job fit score")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation time")
    cv_version: int = Field(..., description="CV iteration number")
    job_url: str = Field(..., description="Job posting URL")
    meets_thresholds: bool = Field(..., description="Whether scores meet minimum thresholds")
    
    def model_dump(self, **kwargs: Any) -> Dict:
        """Override model_dump to handle datetime serialization."""
        dump = super().model_dump(**kwargs)
        # Convert datetime to ISO format string
        if "generated_at" in dump and isinstance(dump["generated_at"], datetime):
            dump["generated_at"] = dump["generated_at"].isoformat()
        return dump
