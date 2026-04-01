"""CV data models."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class PersonalInfo(BaseModel):
    """Personal information for CV."""
    
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    location: Optional[str] = Field(None, description="Location/City")
    website: Optional[str] = Field(None, description="Personal website")


class Experience(BaseModel):
    """Work experience entry."""
    
    company: str = Field(..., description="Company name")
    role: str = Field(..., description="Job title/role")
    start_date: str = Field(..., description="Start date (YYYY-MM)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM) or 'Present'")
    achievements: List[str] = Field(default_factory=list, description="Key achievements")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    location: Optional[str] = Field(None, description="Job location")


class Education(BaseModel):
    """Education entry."""
    
    institution: str = Field(..., description="Institution name")
    degree: str = Field(..., description="Degree/qualification")
    field_of_study: Optional[str] = Field(None, description="Field of study")
    graduation_date: Optional[str] = Field(None, description="Graduation date (YYYY-MM)")
    grade: Optional[str] = Field(None, description="Grade/classification")


class CVData(BaseModel):
    """Complete CV data structure."""
    
    personal_info: PersonalInfo = Field(..., description="Personal information")
    experience: List[Experience] = Field(default_factory=list, description="Work experience")
    education: List[Education] = Field(default_factory=list, description="Education history")
    skills: List[str] = Field(default_factory=list, description="Technical skills")
    certifications: List[str] = Field(default_factory=list, description="Certifications")
    projects: List[dict] = Field(default_factory=list, description="Personal projects")
    summary: Optional[str] = Field(None, description="Professional summary")
    
    # Generated content
    tailored_summary: Optional[str] = Field(None, description="Job-tailored summary")
    html_content: Optional[str] = Field(None, description="Rendered HTML for PDF")
    
    class Config:
        json_schema_extra = {
            "example": {
                "personal_info": {
                    "name": "John Doe",
                    "email": "john.doe@email.com",
                    "phone": "+44 7700 900000",
                    "linkedin": "linkedin.com/in/johndoe",
                },
                "experience": [
                    {
                        "company": "Tech Corp",
                        "role": "Senior Engineer",
                        "start_date": "2020-01",
                        "end_date": "Present",
                        "achievements": ["Led team of 5 developers", "Reduced latency by 40%"],
                        "technologies": ["Python", "AWS", "Kubernetes"],
                    }
                ],
                "skills": ["Python", "JavaScript", "AWS", "Docker", "Kubernetes"],
            }
        }
