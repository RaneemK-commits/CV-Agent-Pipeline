"""Mock provider for testing without external APIs."""

from typing import Optional, List, Dict, Any
from loguru import logger

from src.providers.base_provider import BaseProvider, ProviderConfig
from src.models.job import JobData


class MockProvider(BaseProvider):
    """Mock provider for testing the pipeline without real LLM calls."""
    
    name = "mock"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._initialized = True
    
    async def initialize(self) -> bool:
        """Mock initialization."""
        self._initialized = True
        logger.info("Mock provider initialized")
        return True
    
    async def close(self) -> None:
        """Close mock provider."""
        self._initialized = False
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Return mock chat response."""
        logger.info(f"Mock chat called with {len(messages)} messages")
        
        # Generate context-aware mock responses
        last_message = messages[-1]["content"].lower() if messages else ""
        
        if "job" in last_message and "extract" in last_message:
            return '''```json
{
    "title": "Senior Software Engineer",
    "company": "Tech Innovations Ltd",
    "location": "London, UK",
    "description": "We are seeking an experienced software engineer to join our team.",
    "requirements": ["5+ years Python experience", "AWS knowledge", "Team leadership"],
    "nice_to_have": ["Kubernetes", "Machine Learning"],
    "salary": "£80,000 - £100,000"
}
```'''
        
        if "cv" in last_message and "tailored" in last_message:
            return '''```json
{
    "tailored_summary": "Senior Software Engineer with 6+ years of experience building scalable web applications using Python and AWS. Proven track record of leading teams and delivering high-impact projects.",
    "highlighted_achievements": [
        {"company": "Tech Corp", "achievements": ["Led team of 5 developers", "Reduced latency by 40%"]}
    ],
    "relevant_skills": ["Python", "AWS", "Leadership", "Docker"],
    "suggested_emphasis": "Emphasize leadership experience and AWS expertise"
}
```'''
        
        if "ats" in last_message or "score" in last_message:
            return '''```json
{
    "overall_score": 85,
    "checks": {"contact_info_present": true, "standard_headings": true},
    "flags": [],
    "suggestions": ["Add more keywords from job description"]
}
```'''
        
        if "fit" in last_message or "match" in last_message:
            return '''```json
{
    "overall_score": 82,
    "skill_match_percentage": 80,
    "matched_skills": ["Python", "AWS", "Team Leadership"],
    "missing_skills": ["Kubernetes"],
    "experience_alignment": "Strong match - candidate exceeds requirements",
    "gaps": ["Limited Kubernetes experience"],
    "strengths": ["Strong Python background", "Proven leadership", "AWS expertise"],
    "recommendation": "Excellent candidate - recommend for interview"
}
```'''
        
        if "improve" in last_message or "refine" in last_message:
            return '''```json
{
    "summary_improvement": "Enhanced summary with more keywords",
    "achievement_enhancements": [
        {"company": "Tech Corp", "enhanced_achievements": ["Led team of 5 developers to deliver microservices platform", "Reduced API latency by 40% through optimization"]}
    ],
    "skills_to_add": ["Microservices", "CI/CD"],
    "emphasis_notes": "Focus on leadership and technical impact"
}
```'''
        
        # Default response
        return "This is a mock response for testing purposes."
    
    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Return mock completion response."""
        logger.info(f"Mock complete called with prompt length: {len(prompt)}")
        return await self.chat([{"role": "user", "content": prompt}], model, temperature, max_tokens, **kwargs)
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> List[float]:
        """Return mock embedding (zeros)."""
        logger.info(f"Mock embed called with text length: {len(text)}")
        # Return a simple zero embedding of size 384 (common embedding size)
        return [0.0] * 384
    
    def get_mock_job(self) -> JobData:
        """Return a mock job for testing."""
        from datetime import datetime
        return JobData(
            title="Senior Software Engineer",
            company="Tech Innovations Ltd",
            location="London, UK",
            description="We are seeking an experienced software engineer to join our team. You will work with Python, AWS, and lead a team of developers.",
            requirements=["5+ years Python experience", "AWS knowledge", "Team leadership"],
            nice_to_have=["Kubernetes", "Machine Learning"],
            salary="£80,000 - £100,000",
            url="https://example.com/jobs/test-123",
            scraped_at=datetime.now(),
        )
