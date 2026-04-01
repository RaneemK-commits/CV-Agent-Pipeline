"""Scraper Agent - Extract job details from posting URLs."""

import httpx
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup
from loguru import logger

from src.agents.base_agent import BaseAgent, AgentConfig
from src.models.job import JobData


class ScraperAgent(BaseAgent):
    """Agent for scraping job postings from URLs."""
    
    name = "scraper_agent"
    
    # Supported job site selectors
    SITE_SELECTORS = {
        "indeed.com": {
            "title": "h1[data-jk]",
            "company": "[data-company-name]",
            "location": "[data-rc-location]",
            "description": "#jobDescriptionText",
        },
        "glassdoor.com": {
            "title": "h1.job-title",
            "company": "[data-test='employer-name']",
            "location": "[data-test='job-location']",
            "description": "[data-test='job-description']",
        },
        "reed.co.uk": {
            "title": "h1.job-title",
            "company": ".employer-link",
            "location": ".job-location",
            "description": "#job-description",
        },
        "totaljobs.com": {
            "title": "h1.job-title",
            "company": "[data-automation='job-detail-company-name']",
            "location": "[data-automation='job-detail-location']",
            "description": "[data-automation='job-detail-description']",
        },
    }
    
    default_system_prompt = """You are a job posting extraction assistant. 
    Extract structured information from job posting HTML content."""
    
    def __init__(self, provider_manager, config: Optional[AgentConfig] = None):
        super().__init__(provider_manager, config)
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; CVAgentBot/1.0; +https://example.com/bot)"
            }
        )
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()
    
    async def _generate_mock_job(self, url: str) -> JobData:
        """Generate mock job data using LLM when scraping fails."""
        prompt = f"""Generate a realistic software engineering job posting for this URL: {url}

Return as JSON:
```json
{{
    "title": "Senior Software Engineer",
    "company": "Tech Company",
    "location": "London, UK",
    "description": "Job description here...",
    "requirements": ["Requirement 1", "Requirement 2"],
    "nice_to_have": ["Nice to have 1"],
    "salary": "Competitive"
}}
```"""
        
        messages = self._build_messages(prompt)
        response = await self._call_llm(messages)
        
        # Parse JSON
        import json
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            data = json.loads(response)
        
        from datetime import datetime
        return JobData(
            title=data.get("title", "Software Engineer"),
            company=data.get("company", "Tech Company"),
            location=data.get("location", "Remote"),
            description=data.get("description", ""),
            requirements=data.get("requirements", []),
            nice_to_have=data.get("nice_to_have", []),
            salary=data.get("salary"),
            url=url,
            scraped_at=datetime.now(),
        )
    
    async def execute(self, job_url: str) -> JobData:
        """Scrape job posting from URL.
        
        Args:
            job_url: URL of job posting
            
        Returns:
            Structured job data
        """
        logger.info(f"Scraping job posting: {job_url}")
        
        # Check if using mock provider
        if self.provider_manager.get_provider("mock") and self.provider_manager.get_provider("mock").is_available():
            logger.info("Using mock provider - returning mock job data")
            mock_provider = self.provider_manager.get_provider("mock")
            return mock_provider.get_mock_job()
        
        # Try to fetch the page
        try:
            html = await self._fetch_page(job_url)
        except Exception as fetch_error:
            # If fetching fails and Ollama is available, use LLM to generate mock job
            if self.provider_manager.get_provider("ollama"):
                logger.warning(f"Could not fetch URL, generating job data with LLM: {fetch_error}")
                return await self._generate_mock_job(job_url)
            raise
        
        # Extract site-specific content
        site = self._get_site_domain(job_url)
        selectors = self.SITE_SELECTORS.get(site)
        
        if selectors:
            job_data = self._extract_with_selectors(html, selectors, job_url)
        else:
            # Generic extraction for unknown sites
            job_data = await self._extract_with_llm(html, job_url)
        
        logger.info(f"Extracted job: {job_data.title} at {job_data.company}")
        return job_data
    
    async def _fetch_page(self, url: str) -> str:
        """Fetch HTML content from URL."""
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to fetch job posting: {e}")
    
    def _get_site_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    def _extract_with_selectors(
        self,
        html: str,
        selectors: Dict[str, str],
        url: str,
    ) -> JobData:
        """Extract job data using CSS selectors."""
        soup = BeautifulSoup(html, "lxml")
        
        def get_text(selector: str) -> str:
            el = soup.select_one(selector)
            return el.get_text(strip=True) if el else ""
        
        def get_texts(selector: str) -> list:
            return [el.get_text(strip=True) for el in soup.select(selector)]
        
        title = get_text(selectors.get("title", "h1"))
        company = get_text(selectors.get("company", ""))
        location = get_text(selectors.get("location", ""))
        description = get_text(selectors.get("description", ""))
        
        # Try to extract requirements
        requirements = get_texts("li")[:20]  # Limit to first 20 items
        
        return JobData(
            title=title or "Unknown Position",
            company=company or "Unknown Company",
            location=location or "Not specified",
            description=description or html[:5000],  # Fallback to raw HTML
            requirements=requirements,
            url=url,
        )
    
    async def _extract_with_llm(self, html: str, url: str) -> JobData:
        """Use LLM to extract job data from HTML."""
        # Truncate HTML if too long
        max_html = 15000
        truncated_html = html[:max_html] if len(html) > max_html else html
        
        prompt = f"""Extract job information from this HTML and return as JSON:

```json
{{
    "title": "job title",
    "company": "company name", 
    "location": "location",
    "description": "brief description",
    "requirements": ["requirement 1", "requirement 2"],
    "nice_to_have": ["nice to have 1"],
    "salary": "salary if mentioned"
}}
```

HTML content:
{truncated_html}

Return ONLY the JSON, no other text."""
        
        messages = self._build_messages(prompt)
        response = await self._call_llm(messages)
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response
        
        try:
            data = json.loads(json_str)
            return JobData(
                title=data.get("title", "Unknown Position"),
                company=data.get("company", "Unknown Company"),
                location=data.get("location", "Not specified"),
                description=data.get("description", ""),
                requirements=data.get("requirements", []),
                nice_to_have=data.get("nice_to_have", []),
                salary=data.get("salary"),
                url=url,
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            # Fallback to basic extraction
            return JobData(
                title="Unknown Position",
                company="Unknown Company",
                location="Not specified",
                description=truncated_html,
                url=url,
            )
