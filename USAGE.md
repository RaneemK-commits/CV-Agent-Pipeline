# CV Agent Pipeline - Usage Guide

## Quick Start

### Option 1: Web Interface (Recommended)

The easiest way to use the CV Agent Pipeline is through the web interface.

1. **Start the web server:**
   
   Double-click `start-web.bat` (Windows)
   
   OR run:
   ```bash
   python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000
   ```

2. **Open your browser:**
   ```
   http://localhost:8000
   ```

3. **Generate a CV:**
   - Enter a job posting URL (Indeed, Glassdoor, etc.)
   - Optionally upload your experience YAML file
   - Click "Generate CV"
   - Watch the progress in real-time
   - View ATS and Job Fit scores
   - Preview and download your CV

### Option 2: Command Line (CLI)

```bash
# Generate CV for a job posting
cv-agent generate "https://www.indeed.com/viewjob?jk=123"

# With custom experience file
cv-agent generate "https://www.indeed.com/viewjob?jk=123" \
  --experience my_experience.yaml

# With custom output directory
cv-agent generate "https://www.indeed.com/viewjob?jk=123" \
  --output ./my-cvs
```

### Option 3: Python API

For advanced users who want to integrate the pipeline into their own applications:

```python
import asyncio
from pathlib import Path
from src.utils.config_loader import load_config
from src.pipeline.orchestrator import PipelineOrchestrator

async def generate_my_cv():
    # Load configuration
    config = load_config(Path("config/config.yaml"))
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(config)
    
    # Generate CV
    result = await orchestrator.run(
        job_url="https://www.indeed.com/viewjob?jk=123",
        experience_file=Path("templates/user_experience.yaml"),
    )
    
    print(f"CV generated: {result['cv_path']}")
    print(f"ATS Score: {result['scores']['ats']}")
    print(f"Job Fit Score: {result['scores']['job_fit']}")

# Run
asyncio.run(generate_my_cv())
```

## Step-by-Step Guide

### Step 1: Prepare Your Experience

Fill in the `templates/user_experience.yaml` template with your information:

```yaml
personal_info:
  name: "Your Name"
  email: "your.email@example.com"
  phone: "+1 234 567 8900"
  location: "City, Country"
  linkedin: "linkedin.com/in/yourprofile"
  github: "github.com/yourusername"

experience:
  - company: "Company Name"
    role: "Your Role"
    start_date: "2020-01"
    end_date: "Present"
    location: "City, Country"
    achievements:
      - "Achievement 1 with quantifiable impact"
      - "Improved X by Y%"
    technologies:
      - "Python"
      - "AWS"

education:
  - institution: "University Name"
    degree: "Degree Name"
    field_of_study: "Your Field"
    graduation_date: "2019-06"
    grade: "First Class Honours"

skills:
  - "Skill 1"
  - "Skill 2"
  - "Skill 3"
```

### Step 2: Find a Job Posting

Copy the URL of a job posting from:
- Indeed (indeed.com)
- Glassdoor (glassdoor.com)
- Reed (reed.co.uk)
- Totaljobs (totaljobs.com)
- Company career pages

### Step 3: Generate Your CV

**Via Web Interface:**
1. Open http://localhost:8000
2. Paste the job URL
3. Click "Generate CV"
4. Wait 30-60 seconds
5. Review scores and preview
6. Download

**Via CLI:**
```bash
cv-agent generate "JOB_URL"
```

### Step 4: Review and Iterate

The pipeline automatically:
1. Scrapes the job posting
2. Generates a tailored CV
3. Scores it for ATS compatibility
4. Scores it for job fit
5. Refines if scores are below thresholds

**Score Thresholds:**
- ATS Score: 80/100 minimum
- Job Fit Score: 75/100 minimum

If scores are below thresholds, the pipeline automatically refines the CV (up to 3 iterations).

### Step 5: Use Your CV

Download the CV and:
- Submit with your job application
- Further customize if needed
- Use as a template for similar roles

## API Reference

### Web API Endpoints

If you're building integrations, the web server provides these REST endpoints:

#### Generate CV
```http
POST /api/generate
Content-Type: multipart/form-data

job_url: string
experience: file (optional)
max_iterations: number (default: 3)
```

Response:
```json
{
  "task_id": "task_20260401_123456",
  "status": "pending"
}
```

#### Get Task Status
```http
GET /api/tasks/{task_id}
```

Response:
```json
{
  "task_id": "task_20260401_123456",
  "status": "completed",
  "progress": 100,
  "current_step": "Completed",
  "cv_path": "output/cvs/cv_20260401_123456.html",
  "ats_score": 90,
  "job_fit_score": 85,
  "created_at": "2026-04-01T12:34:56"
}
```

#### List CVs
```http
GET /api/cvs
```

#### Download CV
```http
GET /api/cvs/{filename}
```

## Configuration

### Provider Configuration (`config/providers.yaml`)

Switch between AI providers:

```yaml
providers:
  ollama:
    enabled: true
    default_model: "llama3:8b"
  
  openai:
    enabled: false
    api_key_env: "OPENAI_API_KEY"
    default_model: "gpt-4o"

fallback_chain:
  - ollama
  - openai
```

### Score Thresholds (`config/thresholds.yaml`)

Adjust minimum scores:

```yaml
scoring:
  ats:
    minimum_score: 80
  job_fit:
    minimum_score: 75

refinement:
  max_iterations: 3
```

## Troubleshooting

### Web Interface Won't Load

1. Check server is running: `curl http://localhost:8000/api/health`
2. Check port 8000 is not in use
3. Try: `python -m uvicorn src.web.api:app --reload`

### CV Generation Fails

1. Check Ollama is running: `ollama list`
2. Check job URL is valid
3. Try with a different job site
4. Check logs in `output/logs/`

### Low Scores

If scores are consistently low:

1. **Add more detail to experience** - Quantify achievements
2. **Match keywords** - Include skills from job descriptions
3. **Adjust thresholds** - Edit `config/thresholds.yaml`
4. **Use better model** - Try `llama3:70b` or GPT-4

### PDF Rendering Issues

WeasyPrint requires GTK3 runtime on Windows:
- Download: https://github.com/tschoonj/GTK-for-Windows
- Or use HTML output (works without GTK3)

## Best Practices

### Writing Your Experience

✅ **DO:**
- Quantify achievements ("Increased sales by 25%")
- Use action verbs ("Led", "Built", "Optimized")
- Include relevant technologies
- Keep dates consistent (YYYY-MM format)

❌ **DON'T:**
- Leave achievements vague
- Use passive language
- Omit key skills
- Mix date formats

### Job Selection

✅ **GOOD:**
- Jobs that match 60%+ of your skills
- Clear, detailed job descriptions
- Realistic requirements

❌ **AVOID:**
- Jobs requiring 100% skill match (unrealistic)
- Vague job postings
- Jobs way outside your experience level

### CV Review

Always review generated CVs for:
- Factual accuracy
- Appropriate tone
- Relevant emphasis
- No hallucinated details

## Support

For issues, questions, or feature requests, check:
- GitHub Issues
- Documentation: `PDR.md` for full design details
- Code comments in `src/`

## Next Steps

1. **Generate your first CV** - Try the web interface
2. **Customize experience** - Make it truly yours
3. **Experiment with providers** - Try different LLMs
4. **Adjust thresholds** - Find your sweet spot
5. **Build your portfolio** - Generate CVs for different roles

Happy job hunting! 🚀
