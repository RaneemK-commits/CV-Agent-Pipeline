"""Tests for validators."""

import pytest
from src.utils.validators import (
    validate_job_url,
    validate_experience,
    validate_score_thresholds,
    sanitize_text,
)


class TestValidateJobUrl:
    """Tests for job URL validation."""
    
    def test_valid_indeed_url(self):
        """Test valid Indeed URL."""
        is_valid, error = validate_job_url("https://www.indeed.com/viewjob?jk=123")
        assert is_valid is True
        assert error is None
    
    def test_valid_glassdoor_url(self):
        """Test valid Glassdoor URL."""
        is_valid, error = validate_job_url("https://www.glassdoor.com/job/123")
        assert is_valid is True
    
    def test_invalid_url_no_scheme(self):
        """Test URL without scheme."""
        is_valid, error = validate_job_url("example.com/job/123")
        assert is_valid is False
        assert "http" in error
    
    def test_invalid_url_empty(self):
        """Test empty URL."""
        is_valid, error = validate_job_url("")
        assert is_valid is False
        assert "required" in error


class TestValidateExperience:
    """Tests for experience validation."""
    
    def test_valid_experience(self):
        """Test valid experience data."""
        experience = {
            "personal_info": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+44 7700 900000",
            },
            "experience": [
                {
                    "company": "Tech Corp",
                    "role": "Engineer",
                    "start_date": "2020-01",
                }
            ],
            "skills": ["Python"],
        }
        
        is_valid, errors = validate_experience(experience)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_name(self):
        """Test experience with missing name."""
        experience = {
            "personal_info": {
                "email": "john@example.com",
                "phone": "+44 7700 900000",
            },
            "experience": [],
        }
        
        is_valid, errors = validate_experience(experience)
        assert is_valid is False
        assert "Name is required" in errors
    
    def test_invalid_email(self):
        """Test experience with invalid email."""
        experience = {
            "personal_info": {
                "name": "John Doe",
                "email": "invalid-email",
                "phone": "+44 7700 900000",
            },
            "experience": [],
        }
        
        is_valid, errors = validate_experience(experience)
        assert is_valid is False
        assert "Invalid email format" in errors


class TestValidateScoreThresholds:
    """Tests for score threshold validation."""
    
    def test_scores_meet_thresholds(self):
        """Test scores that meet thresholds."""
        thresholds = {
            "scoring": {
                "ats": {"minimum_score": 80},
                "job_fit": {"minimum_score": 75},
            }
        }
        
        is_valid, issues = validate_score_thresholds(85, 80, thresholds)
        assert is_valid is True
        assert len(issues) == 0
    
    def test_scores_below_thresholds(self):
        """Test scores below thresholds."""
        thresholds = {
            "scoring": {
                "ats": {"minimum_score": 80},
                "job_fit": {"minimum_score": 75},
            }
        }
        
        is_valid, issues = validate_score_thresholds(70, 60, thresholds)
        assert is_valid is False
        assert len(issues) == 2


class TestSanitizeText:
    """Tests for text sanitization."""
    
    def test_sanitize_removes_control_chars(self):
        """Test control character removal."""
        text = "Hello\x00World"
        sanitized = sanitize_text(text)
        assert "\x00" not in sanitized
        assert sanitized == "HelloWorld"
    
    def test_sanitize_normalizes_whitespace(self):
        """Test whitespace normalization."""
        text = "Hello    World\n\nTest"
        sanitized = sanitize_text(text)
        # Multiple spaces become single space, newlines are removed
        assert "Hello" in sanitized
        assert "World" in sanitized
        assert "Test" in sanitized
        assert sanitized.count("  ") == 0  # No double spaces
    
    def test_sanitize_truncates_long_text(self):
        """Test truncation of long text."""
        text = "A" * 200
        sanitized = sanitize_text(text, max_length=100)
        assert len(sanitized) <= 100
        assert "[truncated]" in sanitized
