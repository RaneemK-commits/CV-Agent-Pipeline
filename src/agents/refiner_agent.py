"""Refiner Agent - Improve CV based on scoring feedback."""

import json
import re
from typing import Any, Dict, List, Optional
from loguru import logger

from src.agents.base_agent import BaseAgent, AgentConfig
from src.models.job import JobData
from src.models.cv import CVData
from src.models.scores import ScoreReport


class RefinerAgent(BaseAgent):
    """Agent for refining CV based on score feedback."""
    
    name = "refiner_agent"
    
    default_system_prompt = """You are an expert CV editor.
    Your task is to improve CVs based on ATS and job fit feedback.
    Make targeted improvements while maintaining authenticity."""
    
    def __init__(self, provider_manager, config: Optional[AgentConfig] = None):
        super().__init__(provider_manager, config or AgentConfig(
            temperature=0.7,
            max_tokens=2500,
        ))
    
    async def execute(
        self,
        cv_data: CVData,
        job_data: JobData,
        score_report: ScoreReport,
        iteration: int = 1,
    ) -> CVData:
        """Refine CV based on scoring feedback.
        
        Args:
            cv_data: Current CV data
            job_data: Job posting data
            score_report: Current score report
            iteration: Refinement iteration number
            
        Returns:
            Improved CV data
        """
        logger.info(f"Refining CV (iteration {iteration})")
        
        # Build prompt with feedback
        prompt = self._build_refinement_prompt(cv_data, job_data, score_report, iteration)
        messages = self._build_messages(prompt)
        
        # Get refinement suggestions
        response = await self._call_llm(messages)
        
        # Apply refinements
        refined_cv = self._apply_refinements(cv_data, response, job_data)
        
        logger.info("CV refinement complete")
        return refined_cv
    
    def _build_refinement_prompt(
        self,
        cv_data: CVData,
        job_data: JobData,
        score_report: ScoreReport,
        iteration: int,
    ) -> str:
        """Build prompt for refinement."""
        ats = score_report.ats
        job_fit = score_report.job_fit
        
        prompt = f"""I need you to improve this CV based on scoring feedback.

## Current Scores
- ATS Score: {ats.overall_score}/100
- Job Fit Score: {job_fit.overall_score}/100
- Iteration: {iteration} of 3

## ATS Feedback
Flags: {', '.join(ats.flags) if ats.flags else 'None'}
Suggestions: {', '.join(ats.suggestions[:3]) if ats.suggestions else 'None'}

## Job Fit Feedback
Matched Skills: {', '.join(job_fit.matched_skills[:5]) if job_fit.matched_skills else 'None'}
Missing Skills: {', '.join(job_fit.missing_skills[:5]) if job_fit.missing_skills else 'None'}
Gaps: {', '.join(job_fit.gaps[:3]) if job_fit.gaps else 'None'}
Strengths: {', '.join(job_fit.strengths[:3]) if job_fit.strengths else 'None'}

## Job Requirements
Title: {job_data.title}
Key Requirements:
{chr(10).join(f"- {r}" for r in job_data.requirements[:8])}

## Current CV Summary
- Name: {cv_data.personal_info.name}
- Experience: {len(cv_data.experience)} roles
- Skills: {', '.join(cv_data.skills[:10])}
- Has Summary: {bool(cv_data.summary)}

## Your Task
Provide specific improvements to address the gaps and improve scores.
Focus on:
1. Adding missing keywords from job requirements (naturally, don't force)
2. Emphasizing relevant achievements that match job needs
3. Addressing the specific gaps mentioned
4. Improving ATS compatibility if flagged

Return improvements as JSON:
```json
{{
    "summary_improvement": "Revised professional summary",
    "achievement_enhancements": [
        {{
            "company": "Company Name",
            "enhanced_achievements": ["Enhanced achievement 1", "Enhanced achievement 2"]
        }}
    ],
    "skills_to_add": ["skill1", "skill2"],
    "emphasis_notes": "What aspects to emphasize for this role"
}}
```

Return ONLY the JSON."""
        
        return prompt
    
    def _apply_refinements(
        self,
        cv_data: CVData,
        llm_response: str,
        job_data: JobData,
    ) -> CVData:
        """Apply LLM-suggested refinements to CV."""
        # Extract JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = llm_response
        
        try:
            refinements = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Failed to parse refinement JSON, returning original CV")
            return cv_data
        
        # Apply summary improvement
        if refinements.get("summary_improvement"):
            cv_data.summary = refinements["summary_improvement"]
        
        # Apply achievement enhancements
        enhancements = {
            h["company"]: h["enhanced_achievements"]
            for h in refinements.get("achievement_enhancements", [])
        }
        
        for exp in cv_data.experience:
            if exp.company in enhancements:
                exp.achievements = enhancements[exp.company]
        
        # Add new skills
        existing_skills = set(cv_data.skills)
        new_skills = refinements.get("skills_to_add", [])
        for skill in new_skills:
            if skill.lower() not in [s.lower() for s in existing_skills]:
                cv_data.skills.append(skill)
        
        return cv_data
    
    async def should_continue(self, score_report: ScoreReport, iteration: int) -> bool:
        """Determine if another refinement iteration is needed.
        
        Args:
            score_report: Current score report
            iteration: Current iteration number
            
        Returns:
            True if should continue refining
        """
        max_iterations = 3
        
        if iteration >= max_iterations:
            return False
        
        ats_threshold = 80
        job_fit_threshold = 75
        
        if score_report.ats.overall_score >= ats_threshold and \
           score_report.job_fit.overall_score >= job_fit_threshold:
            return False
        
        return True
