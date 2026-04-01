"""Renderer Agent - Convert CV content to PDF."""

from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
from loguru import logger

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.agents.base_agent import BaseAgent, AgentConfig
from src.models.cv import CVData


class RendererAgent(BaseAgent):
    """Agent for rendering CV to PDF."""
    
    name = "renderer_agent"
    
    default_system_prompt = """You are a CV formatting assistant.
    Convert CV data into clean, professional HTML format."""
    
    def __init__(
        self,
        provider_manager,
        config: Optional[AgentConfig] = None,
        template_dir: Optional[str] = None,
    ):
        super().__init__(provider_manager, config)
        
        # Set up Jinja2 environment
        self.template_dir = template_dir or Path(__file__).parent.parent / "rendering" / "templates"
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
    
    async def execute(
        self,
        cv_data: CVData,
        output_path: Optional[str] = None,
    ) -> Dict[str, str]:
        """Render CV to HTML and optionally PDF.
        
        Args:
            cv_data: CV data to render
            output_path: Optional path for PDF output
            
        Returns:
            Dict with 'html' and optionally 'pdf' paths
        """
        logger.info("Rendering CV to HTML")
        
        # Render HTML
        html_content = self._render_html(cv_data)
        
        result = {"html_content": html_content}
        
        # Render PDF if output path specified
        if output_path:
            pdf_path = self._render_pdf(html_content, output_path)
            result["pdf_path"] = str(pdf_path)
            logger.info(f"PDF saved to: {pdf_path}")
        
        return result
    
    def _render_html(self, cv_data: CVData) -> str:
        """Render CV data to HTML."""
        try:
            template = self.env.get_template("cv_template.html")
        except Exception:
            # Fallback to inline template if file not found
            template = self.env.from_string(self._get_inline_template())
        
        return template.render(
            cv=cv_data,
            today=datetime.now().strftime("%Y-%m-%d"),
        )
    
    def _render_pdf(self, html_content: str, output_path: str) -> Path:
        """Render HTML to PDF using WeasyPrint."""
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            # Configure output path
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            
            # Render with CSS
            font_config = FontConfiguration()
            
            # Get CSS from template or use default
            css_path = self.template_dir / "styles" / "cv_styles.css"
            if css_path.exists():
                css = CSS(str(css_path), font_config=font_config)
            else:
                css = CSS(string=self._get_inline_css(), font_config=font_config)
            
            # Generate PDF
            html = HTML(string=html_content)
            html.write_pdf(str(output), stylesheets=[css])
            
            return output
            
        except ImportError:
            logger.warning("WeasyPrint not installed, saving HTML only")
            output = Path(output_path).with_suffix(".html")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(html_content)
            return output
        except Exception as e:
            logger.error(f"PDF rendering failed: {e}")
            # Fallback to HTML
            output = Path(output_path).with_suffix(".html")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(html_content)
            return output
    
    def _get_inline_template(self) -> str:
        """Fallback inline HTML template."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ cv.personal_info.name }} - CV</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 25px; }
        .contact { color: #7f8c8d; margin-bottom: 20px; }
        .job { margin-bottom: 20px; }
        .job-title { font-weight: bold; color: #2c3e50; }
        .company { color: #3498db; }
        .date { color: #95a5a6; font-size: 0.9em; }
        ul { margin: 5px 0; }
        li { margin: 3px 0; }
    </style>
</head>
<body>
    <h1>{{ cv.personal_info.name }}</h1>
    
    <div class="contact">
        {{ cv.personal_info.email }} | {{ cv.personal_info.phone }}
        {% if cv.personal_info.location %} | {{ cv.personal_info.location }}{% endif %}
        {% if cv.personal_info.linkedin %} | LinkedIn: {{ cv.personal_info.linkedin }}{% endif %}
    </div>
    
    {% if cv.summary %}
    <h2>Professional Summary</h2>
    <p>{{ cv.summary }}</p>
    {% endif %}
    
    <h2>Experience</h2>
    {% for exp in cv.experience %}
    <div class="job">
        <div class="job-title">{{ exp.role }}</div>
        <div class="company">{{ exp.company }} {% if exp.location %} | {{ exp.location }}{% endif %}</div>
        <div class="date">{{ exp.start_date }} - {{ exp.end_date or 'Present' }}</div>
        <ul>
            {% for achievement in exp.achievements %}
            <li>{{ achievement }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endfor %}
    
    <h2>Education</h2>
    {% for edu in cv.education %}
    <div class="job">
        <div class="job-title">{{ edu.degree }} {% if edu.field_of_study %} in {{ edu.field_of_study }}{% endif %}</div>
        <div class="company">{{ edu.institution }} {% if edu.grade %} | {{ edu.grade }}{% endif %}</div>
        <div class="date">{{ edu.graduation_date or 'Expected' }}</div>
    </div>
    {% endfor %}
    
    <h2>Skills</h2>
    <p>{{ cv.skills | join(', ') }}</p>
    
    {% if cv.certifications %}
    <h2>Certifications</h2>
    <ul>
        {% for cert in cv.certifications %}
        <li>{{ cert }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
"""
    
    def _get_inline_css(self) -> str:
        """Fallback inline CSS."""
        return """
        @page {
            size: A4;
            margin: 20mm;
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            font-size: 24pt;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            font-size: 14pt;
            margin-top: 25px;
            border-bottom: 1px solid #ecf0f1;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        """
