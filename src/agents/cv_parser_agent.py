"""CV Parser Agent - Extract structured data from CVs and plain text."""

import re
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from loguru import logger

from src.agents.base_agent import BaseAgent, AgentConfig
from src.models.cv import CVData, PersonalInfo, Experience, Education


class CVParserAgent(BaseAgent):
    """Agent for parsing CVs and plain text into structured data."""
    
    name = "cv_parser_agent"
    
    default_system_prompt = """You are a CV/resume parsing expert.
    Extract structured information from CV text and convert it to JSON format."""
    
    def __init__(self, provider_manager, config: Optional[AgentConfig] = None):
        super().__init__(provider_manager, config or AgentConfig(
            temperature=0.3,
            max_tokens=3000,
        ))
    
    async def execute(
        self,
        cv_text: str,
        source_type: str = "text",  # text, pdf, docx
    ) -> Dict[str, Any]:
        """Parse CV text into structured data.
        
        Args:
            cv_text: Raw CV text content
            source_type: Source type (text, pdf, docx)
            
        Returns:
            Structured experience data in YAML-compatible dict format
        """
        logger.info(f"Parsing CV from {source_type}")
        
        # First try rule-based extraction (faster, no LLM needed)
        parsed = self._rule_based_parse(cv_text)
        
        # If rule-based extraction is incomplete, use LLM
        if self._is_incomplete(parsed):
            logger.info("Rule-based parsing incomplete, using LLM...")
            parsed = await self._llm_parse(cv_text)
        
        # Merge and enhance
        parsed = self._enhance_parsing(parsed, cv_text)
        
        logger.info(f"Parsed CV: {parsed.get('personal_info', {}).get('name', 'Unknown')}")
        return parsed
    
    def _rule_based_parse(self, text: str) -> Dict[str, Any]:
        """Extract information using regex patterns."""
        result = {
            "personal_info": {},
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
        }
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            result["personal_info"]["email"] = email_match.group(0)
        
        # Extract phone (various formats)
        phone_patterns = [
            r'\+?\d[\d\s\-\(\)]{8,}\d',
            r'\(\d{3,4}\)\s*\d{3,4}[\s\-]?\d{3,4}',
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                result["personal_info"]["phone"] = phone_match.group(0)
                break
        
        # Extract LinkedIn
        linkedin_match = re.search(r'linkedin\.com/in/[\w\-]+', text)
        if linkedin_match:
            result["personal_info"]["linkedin"] = linkedin_match.group(0)
        
        # Extract GitHub
        github_match = re.search(r'github\.com/[\w\-]+', text)
        if github_match:
            result["personal_info"]["github"] = github_match.group(0)
        
        # Extract name (usually at the top, capitalized)
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 100 and not any(x in line.lower() for x in ['@', 'http', 'phone']):
                # Likely a name
                if line[0].isupper() and not line.isdigit():
                    result["personal_info"]["name"] = line
                    break
        
        # Extract skills (look for skill sections)
        skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'react', 'angular', 'vue', 'node', 'django', 'flask',
            'sql', 'mongodb', 'postgresql', 'mysql',
            'git', 'linux', 'agile', 'scrum'
        ]
        
        found_skills = []
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        result["skills"] = list(set(found_skills))
        
        return result
    
    def _is_incomplete(self, parsed: Dict[str, Any]) -> bool:
        """Check if parsing result is incomplete."""
        # Need at least name and some experience
        if not parsed.get("personal_info", {}).get("name"):
            return True
        if not parsed.get("experience") or len(parsed["experience"]) == 0:
            return True
        return False
    
    async def _llm_parse(self, text: str) -> Dict[str, Any]:
        """Use LLM to parse CV text."""
        # Truncate if too long
        max_chars = 10000
        if len(text) > max_chars:
            text = text[:max_chars] + "... [truncated]"
        
        prompt = f"""Extract structured information from this CV/resume text.

Return the data as JSON with this exact structure:
```json
{{
    "personal_info": {{
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "+1 234 567 8900",
        "location": "City, Country",
        "linkedin": "linkedin.com/in/profile",
        "github": "github.com/username"
    }},
    "experience": [
        {{
            "company": "Company Name",
            "role": "Job Title",
            "start_date": "YYYY-MM",
            "end_date": "YYYY-MM or Present",
            "location": "City, Country",
            "achievements": ["Achievement 1", "Achievement 2"],
            "technologies": ["Tech1", "Tech2"]
        }}
    ],
    "education": [
        {{
            "institution": "University Name",
            "degree": "Degree Name",
            "field_of_study": "Field",
            "graduation_date": "YYYY-MM",
            "grade": "Grade (optional)"
        }}
    ],
    "skills": ["Skill1", "Skill2", "Skill3"],
    "projects": [
        {{
            "name": "Project Name",
            "description": "Brief description",
            "technologies": ["Tech1", "Tech2"]
        }}
    ],
    "certifications": ["Certification 1", "Certification 2"]
}}
```

CV Text:
{text}

Return ONLY the JSON, no other text."""
        
        messages = self._build_messages(prompt)
        response = await self._call_llm(messages)
        
        # Parse JSON response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}")
            return self._rule_based_parse(text)
    
    def _enhance_parsing(self, parsed: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """Enhance parsed data with additional extraction."""
        # Ensure all required fields exist
        if "personal_info" not in parsed:
            parsed["personal_info"] = {}
        
        if "experience" not in parsed:
            parsed["experience"] = []
        
        if "education" not in parsed:
            parsed["education"] = []
        
        if "skills" not in parsed:
            parsed["skills"] = []
        
        # Clean up dates in experience
        for exp in parsed.get("experience", []):
            if "start_date" in exp:
                exp["start_date"] = self._normalize_date(exp["start_date"])
            if "end_date" in exp:
                exp["end_date"] = self._normalize_date(exp["end_date"])
        
        return parsed
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM format."""
        if not date_str:
            return ""
        
        # Handle "Present"
        if date_str.lower() in ["present", "now", "current"]:
            return "Present"
        
        # Try to extract year-month
        match = re.search(r'(\d{4})[\s\-/](\d{1,2})', date_str)
        if match:
            year, month = match.groups()
            return f"{year}-{int(month):02d}"
        
        # Just year
        match = re.search(r'\b(\d{4})\b', date_str)
        if match:
            return f"{match.group(1)}-01"
        
        return date_str


def parse_cv_file(file_path: Path, cv_parser: CVParserAgent) -> Dict[str, Any]:
    """Parse a CV file (PDF, DOCX, or TXT)."""
    import asyncio
    
    file_ext = file_path.suffix.lower()
    
    if file_ext == '.txt':
        text = file_path.read_text(encoding='utf-8')
        return asyncio.run(cv_parser.execute(text, source_type="text"))
    
    elif file_ext == '.pdf':
        text = extract_text_from_pdf(file_path)
        return asyncio.run(cv_parser.execute(text, source_type="pdf"))
    
    elif file_ext in ['.docx', '.doc']:
        text = extract_text_from_docx(file_path)
        return asyncio.run(cv_parser.execute(text, source_type="docx"))
    
    else:
        # Try as text
        text = file_path.read_text(encoding='utf-8')
        return asyncio.run(cv_parser.execute(text, source_type="text"))


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
        
        text_parts = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text_parts.append(page.extract_text())
        
        return "\n".join(text_parts)
    
    except ImportError:
        logger.warning("PyPDF2 not installed, trying pdfminer")
        try:
            from pdfminer.high_level import extract_text
            return extract_text(str(file_path))
        except ImportError:
            logger.error("No PDF library available")
            return ""
    
    except Exception as e:
        logger.error(f"Failed to extract PDF text: {e}")
        return ""


def extract_text_from_docx(file_path: Path) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document
        
        doc = Document(str(file_path))
        return "\n".join([para.text for para in doc.paragraphs if para.text])
    
    except ImportError:
        logger.error("python-docx not installed")
        return ""
    
    except Exception as e:
        logger.error(f"Failed to extract DOCX text: {e}")
        return ""
