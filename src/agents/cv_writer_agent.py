"""CV Writer Agent - Generate tailored CV content."""

import json
from typing import Any, Dict, List, Optional
from loguru import logger

from src.agents.base_agent import BaseAgent, AgentConfig
from src.models.job import JobData
from src.models.cv import CVData, PersonalInfo, Experience, Education


class CVWriterAgent(BaseAgent):
    """Agent for generating tailored CV content."""
    
    name = "cv_writer_agent"
    
    default_system_prompt = """You are an expert CV writer with 15+ years of experience.
Your task is to create tailored, professional CVs that highlight the candidate's 
most relevant experience for each job.

Guidelines:
- Use action verbs and quantify achievements
- Keep bullet points concise (1-2 lines each)
- Prioritize relevance to the job description
- Maintain a professional, confident tone
- Format output as valid JSON matching the CV schema"""
    
    def __init__(self, provider_manager, config: Optional[AgentConfig] = None):
        super().__init__(provider_manager, config or AgentConfig(
            temperature=0.7,
            max_tokens=2500,
        ))
    
    async def execute(
        self,
        user_experience: Dict[str, Any],
        job_data: JobData,
    ) -> CVData:
        """Generate tailored CV.
        
        Args:
            user_experience: User's raw experience data
            job_data: Job posting data
            
        Returns:
            Tailored CV data
        """
        logger.info(f"Generating CV for job: {job_data.title} at {job_data.company}")
        
        # Build prompt
        prompt = self._build_prompt(user_experience, job_data)
        messages = self._build_messages(prompt)
        
        # Call LLM
        response = await self._call_llm(messages)
        
        # Parse response
        cv_data = self._parse_response(response, user_experience)
        
        logger.info(f"Generated CV with {len(cv_data.experience)} experiences")
        return cv_data
    
    def _build_prompt(
        self,
        user_experience: Dict[str, Any],
        job_data: JobData,
    ) -> str:
        """Build the LLM prompt."""
        job_description = job_data.description[:3000]  # Limit description length
        requirements = "\n".join(f"- {r}" for r in job_data.requirements[:10])
        
        prompt = f"""I need you to create a tailored CV for this job posting.

## Job Posting
**Title:** {job_data.title}
**Company:** {job_data.company}
**Location:** {job_data.location}

**Requirements:**
{requirements}

**Description:**
{job_description}

## My Experience
{json.dumps(user_experience, indent=2)}

## Task
Create a tailored CV that:
1. Writes a compelling professional summary (3-4 lines) targeting this specific role
2. Selects and emphasizes the most relevant achievements from my experience
3. Highlights skills that match the job requirements
4. Uses keywords from the job description naturally

Return the result as JSON with this structure:
```json
{{
    "tailored_summary": "Your 3-4 line professional summary",
    "highlighted_achievements": [
        {{
            "company": "Company Name",
            "achievements": ["Achievement 1", "Achievement 2"]
        }}
    ],
    "relevant_skills": ["skill1", "skill2"],
    "suggested_emphasis": "Brief note on what aspects to emphasize for this role"
}}
```

Focus on making my experience directly relevant to THIS specific job."""
        
        return prompt
    
    def _parse_response(
        self,
        response: str,
        user_experience: Dict[str, Any],
    ) -> CVData:
        """Parse LLM response into CV data."""
        import re
        
        # Extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Failed to parse CV JSON, using fallback")
            data = {}
        
        # Build CV from user experience + LLM suggestions
        personal_info = PersonalInfo(**user_experience.get("personal_info", {}))
        
        # Process experience with highlighted achievements
        experiences = []
        highlighted = {
            h["company"]: h["achievements"] 
            for h in data.get("highlighted_achievements", [])
        }
        
        for exp in user_experience.get("experience", []):
            achievements = highlighted.get(exp.get("company"), exp.get("achievements", []))
            experiences.append(Experience(
                company=exp.get("company", ""),
                role=exp.get("role", ""),
                start_date=exp.get("start_date", ""),
                end_date=exp.get("end_date"),
                achievements=achievements,
                technologies=exp.get("technologies", []),
                location=exp.get("location"),
            ))
        
        # Process education
        education = [
            Education(
                institution=e.get("institution", ""),
                degree=e.get("degree", ""),
                field_of_study=e.get("field_of_study"),
                graduation_date=e.get("graduation_date"),
                grade=e.get("grade"),
            )
            for e in user_experience.get("education", [])
        ]
        
        # Combine skills
        base_skills = set(user_experience.get("skills", []))
        relevant_skills = set(data.get("relevant_skills", []))
        all_skills = list(base_skills | relevant_skills)
        
        return CVData(
            personal_info=personal_info,
            experience=experiences,
            education=education,
            skills=all_skills,
            certifications=user_experience.get("certifications", []),
            projects=user_experience.get("projects", []),
            summary=data.get("tailored_summary"),
        )
