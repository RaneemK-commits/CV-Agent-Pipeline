"""Job Fit Scorer Agent - Score CV relevance against job description."""

import json
import re
from typing import Any, Dict, List, Optional
from loguru import logger

from src.agents.base_agent import BaseAgent, AgentConfig
from src.models.job import JobData
from src.models.cv import CVData
from src.models.scores import JobFitScore


class JobFitScorerAgent(BaseAgent):
    """Agent for scoring CV fit against job description."""
    
    name = "job_fit_scorer_agent"
    
    default_system_prompt = """You are a hiring manager and career expert.
    Evaluate how well a candidate's CV matches a job description.
    Provide honest, constructive assessment of fit and gaps."""
    
    def __init__(self, provider_manager, config: Optional[AgentConfig] = None):
        super().__init__(provider_manager, config or AgentConfig(
            temperature=0.3,  # Lower temperature for consistent scoring
            max_tokens=1500,
        ))
    
    async def execute(
        self,
        cv_data: CVData,
        job_data: JobData,
    ) -> JobFitScore:
        """Score CV against job description.
        
        Args:
            cv_data: CV data
            job_data: Job posting data
            
        Returns:
            Job fit score with detailed analysis
        """
        logger.info(f"Scoring CV fit for: {job_data.title}")
        
        # Use LLM for comprehensive analysis
        analysis = await self._analyze_fit(cv_data, job_data)
        
        # Parse LLM response
        parsed = self._parse_analysis(analysis, job_data)
        
        logger.info(f"Job Fit Score: {parsed.overall_score}/100")
        
        return parsed
    
    async def _analyze_fit(self, cv_data: CVData, job_data: JobData) -> str:
        """Get fit analysis from LLM."""
        # Prepare CV summary
        cv_summary = self._summarize_cv(cv_data)
        
        # Prepare job requirements
        job_summary = self._summarize_job(job_data)
        
        prompt = f"""Analyze how well this CV matches the job requirements.

## Job Requirements
{job_summary}

## Candidate CV Summary
{cv_summary}

## Task
Evaluate the candidate's fit for this role and return a JSON analysis:

```json
{{
    "overall_score": 75,
    "skill_match_percentage": 70,
    "matched_skills": ["Python", "AWS", "Team Leadership"],
    "missing_skills": ["Kubernetes", "Machine Learning"],
    "experience_alignment": "Strong match - candidate has 6 years vs 5 required",
    "gaps": ["Limited experience with containerization", "No ML background mentioned"],
    "strengths": ["Strong Python expertise", "Proven leadership track record", "AWS certified"],
    "recommendation": "Good candidate - consider for interview"
}}
```

Be honest and specific. Score considerations:
- 90-100: Exceptional match, exceeds requirements
- 75-89: Strong match, meets most requirements  
- 60-74: Moderate match, some gaps
- 40-59: Weak match, significant gaps
- 0-39: Poor match, missing key requirements

Return ONLY the JSON."""
        
        messages = self._build_messages(prompt)
        return await self._call_llm(messages)
    
    def _parse_analysis(self, analysis: str, job_data: JobData) -> JobFitScore:
        """Parse LLM analysis into JobFitScore."""
        # Extract JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', analysis, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = analysis
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Failed to parse job fit JSON")
            data = {}
        
        return JobFitScore(
            overall_score=data.get("overall_score", 50),
            skill_match_percentage=data.get("skill_match_percentage", 50),
            matched_skills=data.get("matched_skills", []),
            missing_skills=data.get("missing_skills", []),
            experience_alignment=data.get("experience_alignment", "Unable to assess"),
            gaps=data.get("gaps", []),
            strengths=data.get("strengths", []),
        )
    
    def _summarize_cv(self, cv_data: CVData) -> str:
        """Create CV summary for LLM."""
        summary_parts = []
        
        # Personal
        summary_parts.append(f"Name: {cv_data.personal_info.name}")
        
        # Summary
        if cv_data.summary:
            summary_parts.append(f"Professional Summary: {cv_data.summary}")
        
        # Experience
        summary_parts.append("\nExperience:")
        for exp in cv_data.experience:
            achievements = "\n  - ".join(exp.achievements[:3]) if exp.achievements else "No details"
            summary_parts.append(f"- {exp.role} at {exp.company} ({exp.start_date} - {exp.end_date or 'Present'})")
            summary_parts.append(f"  Key achievements: {achievements}")
            if exp.technologies:
                summary_parts.append(f"  Technologies: {', '.join(exp.technologies)}")
        
        # Skills
        if cv_data.skills:
            summary_parts.append(f"\nSkills: {', '.join(cv_data.skills)}")
        
        # Education
        if cv_data.education:
            summary_parts.append("\nEducation:")
            for edu in cv_data.education:
                degree = f"{edu.degree} in {edu.field_of_study}" if edu.field_of_study else edu.degree
                summary_parts.append(f"- {degree} from {edu.institution}")
        
        return "\n".join(summary_parts)
    
    def _summarize_job(self, job_data: JobData) -> str:
        """Create job summary for LLM."""
        parts = [
            f"Title: {job_data.title}",
            f"Company: {job_data.company}",
            f"Location: {job_data.location}",
        ]
        
        if job_data.requirements:
            parts.append("\nKey Requirements:")
            for req in job_data.requirements[:10]:
                parts.append(f"- {req}")
        
        if job_data.nice_to_have:
            parts.append("\nNice to Have:")
            for nice in job_data.nice_to_have[:5]:
                parts.append(f"- {nice}")
        
        if job_data.description:
            # Truncate description
            desc = job_data.description[:1000]
            parts.append(f"\nDescription: {desc}...")
        
        return "\n".join(parts)
