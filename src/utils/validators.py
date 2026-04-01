"""Input validation utilities."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from loguru import logger


def validate_job_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate a job posting URL.
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"
    
    # Check scheme
    if parsed.scheme not in ("http", "https"):
        return False, "URL must start with http:// or https://"
    
    # Check domain
    if not parsed.netloc:
        return False, "Invalid URL - missing domain"
    
    # Check for known job sites
    known_sites = [
        "indeed.com",
        "glassdoor.com",
        "reed.co.uk",
        "totaljobs.com",
        "linkedin.com",
        "monster.com",
        "simplyhired.com",
    ]
    
    domain = parsed.netloc.lower()
    is_known = any(site in domain for site in known_sites)
    
    if not is_known:
        logger.warning(f"Unknown job site: {domain}. Will attempt generic scraping.")
    
    return True, None


def validate_experience(experience: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate user experience data.
    
    Args:
        experience: Experience dictionary
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    # Check personal info
    personal_info = experience.get("personal_info", {})
    if not personal_info.get("name"):
        errors.append("Name is required")
    if not personal_info.get("email"):
        errors.append("Email is required")
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", personal_info.get("email", "")):
        errors.append("Invalid email format")
    if not personal_info.get("phone"):
        errors.append("Phone number is required")
    
    # Check experience
    work_experience = experience.get("experience", [])
    if not work_experience:
        errors.append("At least one work experience is required")
    else:
        for i, exp in enumerate(work_experience):
            if not exp.get("company"):
                errors.append(f"Experience {i + 1}: Company is required")
            if not exp.get("role"):
                errors.append(f"Experience {i + 1}: Role is required")
            if not exp.get("start_date"):
                errors.append(f"Experience {i + 1}: Start date is required")
    
    # Check skills
    skills = experience.get("skills", [])
    if not skills:
        logger.warning("No skills provided - CV may be less effective")
    
    return len(errors) == 0, errors


def validate_file_path(path: str, must_exist: bool = True) -> Tuple[bool, Optional[str]]:
    """Validate a file path.
    
    Args:
        path: File path to validate
        must_exist: Whether file must already exist
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Path is required"
    
    file_path = Path(path)
    
    if must_exist and not file_path.exists():
        return False, f"File not found: {path}"
    
    # Check parent directory is writable
    try:
        parent = file_path.parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        return True, None
    except Exception as e:
        return False, f"Cannot write to path: {e}"


def validate_score_thresholds(
    ats_score: int,
    job_fit_score: int,
    thresholds: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """Validate scores against thresholds.
    
    Args:
        ats_score: ATS score
        job_fit_score: Job fit score
        thresholds: Threshold configuration
        
    Returns:
        Tuple of (meets_thresholds, list of issues)
    """
    issues = []
    
    ats_threshold = thresholds.get("scoring", {}).get("ats", {}).get("minimum_score", 80)
    job_fit_threshold = thresholds.get("scoring", {}).get("job_fit", {}).get("minimum_score", 75)
    
    if ats_score < ats_threshold:
        issues.append(f"ATS score ({ats_score}) below threshold ({ats_threshold})")
    
    if job_fit_score < job_fit_threshold:
        issues.append(f"Job fit score ({job_fit_score}) below threshold ({job_fit_threshold})")
    
    return len(issues) == 0, issues


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize text for safe processing.
    
    Args:
        text: Text to sanitize
        max_length: Optional maximum length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove control characters
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    
    # Normalize whitespace
    text = " ".join(text.split())
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length - 100] + "...\n[truncated]"
    
    return text
