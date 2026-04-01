"""Tests for CV data models."""

import pytest
from src.models.cv import CVData, PersonalInfo, Experience, Education


class TestPersonalInfo:
    """Tests for PersonalInfo model."""
    
    def test_valid_personal_info(self):
        """Test creating valid personal info."""
        info = PersonalInfo(
            name="John Doe",
            email="john@example.com",
            phone="+44 7700 900000",
        )
        assert info.name == "John Doe"
        assert info.email == "john@example.com"
    
    def test_personal_info_with_optional_fields(self):
        """Test personal info with optional fields."""
        info = PersonalInfo(
            name="John Doe",
            email="john@example.com",
            phone="+44 7700 900000",
            linkedin="linkedin.com/in/johndoe",
            github="github.com/johndoe",
        )
        assert info.linkedin == "linkedin.com/in/johndoe"
        assert info.github == "github.com/johndoe"


class TestExperience:
    """Tests for Experience model."""
    
    def test_valid_experience(self):
        """Test creating valid experience."""
        exp = Experience(
            company="Tech Corp",
            role="Software Engineer",
            start_date="2020-01",
            achievements=["Built feature X", "Improved performance by 20%"],
        )
        assert exp.company == "Tech Corp"
        assert exp.role == "Software Engineer"
        assert exp.end_date is None  # Optional field
    
    def test_experience_with_end_date(self):
        """Test experience with end date."""
        exp = Experience(
            company="Tech Corp",
            role="Software Engineer",
            start_date="2020-01",
            end_date="2022-12",
        )
        assert exp.end_date == "2022-12"


class TestCVData:
    """Tests for CVData model."""
    
    def test_minimal_cv(self):
        """Test creating minimal CV."""
        cv = CVData(
            personal_info=PersonalInfo(
                name="John Doe",
                email="john@example.com",
                phone="+44 7700 900000",
            )
        )
        assert cv.personal_info.name == "John Doe"
        assert len(cv.experience) == 0
        assert len(cv.skills) == 0
    
    def test_complete_cv(self):
        """Test creating complete CV."""
        cv = CVData(
            personal_info=PersonalInfo(
                name="John Doe",
                email="john@example.com",
                phone="+44 7700 900000",
            ),
            experience=[
                Experience(
                    company="Tech Corp",
                    role="Engineer",
                    start_date="2020-01",
                )
            ],
            skills=["Python", "AWS"],
        )
        assert len(cv.experience) == 1
        assert "Python" in cv.skills
