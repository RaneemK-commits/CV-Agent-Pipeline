"""ATS Scorer Agent - Evaluate CV against ATS compatibility rules."""

import re
from typing import Any, Dict, List, Optional
from loguru import logger

from src.agents.base_agent import BaseAgent, AgentConfig
from src.models.cv import CVData
from src.models.scores import ATSScore


class ATSScorerAgent(BaseAgent):
    """Agent for scoring CV against ATS compatibility rules."""
    
    name = "ats_scorer_agent"
    
    default_system_prompt = """You are an ATS (Applicant Tracking System) expert.
    Evaluate CVs for ATS compatibility and provide actionable feedback."""
    
    def __init__(self, provider_manager, config: Optional[AgentConfig] = None):
        super().__init__(provider_manager, config or AgentConfig(
            temperature=0.3,  # Lower temperature for consistent scoring
            max_tokens=1000,
        ))
    
    async def execute(
        self,
        cv_data: CVData,
        html_content: Optional[str] = None,
    ) -> ATSScore:
        """Score CV for ATS compatibility.
        
        Args:
            cv_data: CV data
            html_content: Optional HTML content for additional checks
            
        Returns:
            ATS score with detailed feedback
        """
        logger.info("Scoring CV for ATS compatibility")
        
        checks = {}
        flags = []
        suggestions = []
        score = 0
        
        # Check 1: Contact info present (+10)
        has_contact = self._check_contact_info(cv_data.personal_info)
        checks["contact_info_present"] = has_contact
        if has_contact:
            score += 10
        else:
            flags.append("Missing contact information")
            suggestions.append("Add email, phone, and location to your CV")
        
        # Check 2: Standard section headings (+10)
        has_headings = self._check_standard_headings(cv_data)
        checks["standard_headings"] = has_headings
        if has_headings:
            score += 10
        else:
            flags.append("Non-standard section headings detected")
            suggestions.append("Use standard headings: Experience, Education, Skills")
        
        # Check 3: No images in content (+10)
        no_images = self._check_no_images(html_content)
        checks["no_images_in_content"] = no_images
        if no_images:
            score += 10
        else:
            flags.append("Images detected in CV")
            suggestions.append("Remove images and graphics for ATS compatibility")
        
        # Check 4: Proper date formatting (+10)
        dates_formatted = self._check_date_formatting(cv_data)
        checks["proper_date_formatting"] = dates_formatted
        if dates_formatted:
            score += 10
        else:
            flags.append("Inconsistent date formatting")
            suggestions.append("Use consistent date format (e.g., YYYY-MM or Month YYYY)")
        
        # Check 5: Skills section present (+10)
        has_skills = len(cv_data.skills) > 0
        checks["skills_section_present"] = has_skills
        if has_skills:
            score += 10
        else:
            flags.append("No skills section")
            suggestions.append("Add a dedicated skills section with relevant technologies")
        
        # Check 6: Experience with achievements (+20)
        has_achievements = self._check_achievements(cv_data)
        checks["achievements_present"] = has_achievements
        if has_achievements:
            score += 20
        else:
            flags.append("Missing quantified achievements")
            suggestions.append("Add specific, quantified achievements to each role")
        
        # Check 7: Education section (+10)
        has_education = len(cv_data.education) > 0
        checks["education_present"] = has_education
        if has_education:
            score += 10
        else:
            flags.append("No education section")
            suggestions.append("Add your education history")
        
        # Check 8: Reasonable length (+10)
        reasonable_length = self._check_length(cv_data)
        checks["reasonable_length"] = reasonable_length
        if reasonable_length:
            score += 10
        else:
            flags.append("CV may be too long or too short")
            suggestions.append("Aim for 1-2 pages depending on experience level")
        
        # Check 9: No tables for layout (+5)
        no_tables = self._check_no_tables(html_content)
        checks["no_tables_for_layout"] = no_tables
        if no_tables:
            score += 5
        else:
            flags.append("Tables detected - may confuse ATS")
            suggestions.append("Avoid using tables for layout")
        
        # Check 10: Standard fonts (+5)
        standard_fonts = self._check_standard_fonts(html_content)
        checks["standard_fonts"] = standard_fonts
        if standard_fonts:
            score += 5
        else:
            flags.append("Non-standard fonts detected")
            suggestions.append("Use standard fonts like Arial, Calibri, or Times New Roman")
        
        # Generate additional suggestions using LLM
        llm_suggestions = await self._get_llm_suggestions(cv_data)
        suggestions.extend(llm_suggestions[:3])  # Limit to top 3
        
        logger.info(f"ATS Score: {score}/100")
        
        return ATSScore(
            overall_score=score,
            checks=checks,
            flags=flags,
            suggestions=suggestions,
        )
    
    def _check_contact_info(self, personal_info) -> bool:
        """Check if contact info is complete."""
        has_email = bool(personal_info.email and "@" in personal_info.email)
        has_phone = bool(personal_info.phone)
        return has_email and has_phone
    
    def _check_standard_headings(self, cv_data: CVData) -> bool:
        """Check for standard section headings."""
        has_experience = len(cv_data.experience) > 0
        has_education = len(cv_data.education) > 0
        has_skills = len(cv_data.skills) > 0
        return has_experience and has_education and has_skills
    
    def _check_no_images(self, html_content: Optional[str]) -> bool:
        """Check if HTML contains images."""
        if not html_content:
            return True  # No HTML to check
        return "<img" not in html_content.lower()
    
    def _check_date_formatting(self, cv_data: CVData) -> bool:
        """Check for consistent date formatting."""
        date_pattern = re.compile(r"^\d{4}-\d{2}$|^\w+ \d{4}$|^Present$")
        
        for exp in cv_data.experience:
            if exp.start_date and not date_pattern.match(exp.start_date):
                return False
            if exp.end_date and not date_pattern.match(exp.end_date):
                return False
        
        return True
    
    def _check_achievements(self, cv_data: CVData) -> bool:
        """Check if experiences have achievements."""
        for exp in cv_data.experience:
            if exp.achievements and len(exp.achievements) > 0:
                # Check for quantified achievements (numbers)
                for achievement in exp.achievements:
                    if re.search(r"\d+%|\d+x|\d{3,}", achievement):
                        return True
        return False
    
    def _check_length(self, cv_data: CVData) -> bool:
        """Check if CV length is reasonable."""
        # Count approximate words
        words = 0
        for exp in cv_data.experience:
            for achievement in exp.achievements:
                words += len(achievement.split())
        words += len(" ".join(cv_data.skills))
        
        # 300-1500 words is reasonable
        return 300 <= words <= 1500
    
    def _check_no_tables(self, html_content: Optional[str]) -> bool:
        """Check if HTML uses tables for layout."""
        if not html_content:
            return True
        return "<table" not in html_content.lower()
    
    def _check_standard_fonts(self, html_content: Optional[str]) -> bool:
        """Check for standard fonts."""
        if not html_content:
            return True  # No font info to check
        
        standard_fonts = ["arial", "calibri", "times", "georgia", "verdana", "helvetica"]
        html_lower = html_content.lower()
        
        for font in standard_fonts:
            if font in html_lower:
                return True
        
        return "font-family" not in html_lower or any(f in html_lower for f in standard_fonts)
    
    async def _get_llm_suggestions(self, cv_data: CVData) -> List[str]:
        """Get additional suggestions from LLM."""
        prompt = f"""Review this CV and provide 3 specific suggestions for improving ATS compatibility.
Format as a JSON array of strings.

CV Summary:
- Name: {cv_data.personal_info.name}
- Experience count: {len(cv_data.experience)}
- Skills: {', '.join(cv_data.skills[:10])}
- Has summary: {bool(cv_data.summary)}

Return ONLY a JSON array like: ["suggestion 1", "suggestion 2", "suggestion 3"]"""
        
        try:
            messages = self._build_messages(prompt)
            response = await self._call_llm(messages)
            
            import json
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception as e:
            logger.warning(f"LLM suggestions failed: {e}")
        
        return []
