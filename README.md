# CV Agent Pipeline

A multi-agent AI system that automates the creation of tailored, professional CVs. The system takes your raw experience and a job posting URL, then autonomously generates a customized CV, renders it as a PDF, evaluates ATS compatibility, and scores job fit.

## Features

- 🤖 **Multi-Agent System**: 6 specialized AI agents working together
- 📄 **Tailored CVs**: Automatically customizes your CV for each job
- 📊 **ATS Scoring**: Evaluates CV compatibility with Applicant Tracking Systems
- 🎯 **Job Fit Analysis**: Scores how well your CV matches the job description
- 🔄 **Auto-Refinement**: Iteratively improves CV until quality thresholds are met
- 🌐 **Multi-Provider**: Supports Ollama (local), OpenAI, Anthropic, Groq, Mistral
- 💾 **Vector Store**: Stores past CVs and jobs for pattern learning (ChromaDB)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- For local inference: [Ollama](https://ollama.com) with `llama3:8b` model
- For external APIs: API keys from respective providers

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd CV_Agent_Pipeline
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Ollama (optional, for local inference):**
   ```bash
   # Download from https://ollama.com
   ollama pull llama3:8b
   ollama pull nomic-embed-text
   ```

5. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (if using external providers)
   ```

### Usage

### Web Interface (Recommended)

1. **Start the web server:**
   ```bash
   python -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000
   ```

2. **Open in browser:**
   ```
   http://localhost:8000
   ```

3. **Generate a CV:**
   - Enter a job posting URL
   - Optionally upload your experience YAML
   - Click "Generate CV"
   - View scores and preview your CV
   - Download when ready!

### CLI (Command Line)

1. **Fill in your experience:**
   ```bash
   # Edit templates/user_experience.yaml with your information
   ```

2. **Generate a CV:**
   ```bash
   cv-agent generate <job-posting-url>
   ```

   Example:
   ```bash
   cv-agent generate "https://www.indeed.com/viewjob?jk=12345"
   ```

3. **Find your generated CV:**
   - HTML: `output/cvs/cv_YYYYMMDD_HHMMSS.html`
   - Score Report: `output/reports/report_YYYYMMDD_HHMMSS.json`

## Configuration

### Provider Configuration (`config/providers.yaml`)

Enable/disable providers and set default models:

```yaml
providers:
  ollama:
    enabled: true
    base_url: "http://localhost:11434"
    default_model: "llama3:8b"
  
  openai:
    enabled: false
    api_key_env: "OPENAI_API_KEY"
    default_model: "gpt-4o"

fallback_chain:
  - ollama
  - groq
  - openai
```

### Score Thresholds (`config/thresholds.yaml`)

Set minimum scores required:

```yaml
scoring:
  ats:
    minimum_score: 80
  job_fit:
    minimum_score: 75

refinement:
  max_iterations: 3
```

## Architecture

### Agents

| Agent | Purpose |
|-------|---------|
| **Scraper Agent** | Extracts job details from posting URLs |
| **CV Writer Agent** | Generates tailored CV content |
| **Renderer Agent** | Converts CV to PDF using WeasyPrint |
| **ATS Scorer Agent** | Evaluates ATS compatibility |
| **Job Fit Scorer Agent** | Scores CV against job description |
| **Refiner Agent** | Improves CV based on scores |

### Pipeline Flow

```
User Input → Scrape Job → Generate CV → Render PDF → Score → Refine (if needed) → Output
                ↓                                              ↑
            Store in ChromaDB ←────────────────────────────────┘
```

## CLI Commands

```bash
# Generate a CV for a job posting
cv-agent generate <job-url> [options]

# Initialize a new project
cv-agent init [directory]

# Show version
cv-agent version
```

### Options for `generate`:

| Option | Description |
|--------|-------------|
| `-e, --experience` | Path to experience YAML (default: `templates/user_experience.yaml`) |
| `-c, --config` | Path to config file (default: `config/config.yaml`) |
| `-o, --output` | Output directory (default: from config) |
| `-l, --log-level` | Logging level: DEBUG, INFO, WARNING, ERROR |

## Supported Job Sites

- Indeed
- Glassdoor
- Reed.co.uk
- Totaljobs
- Standard company career pages (generic scraping)

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

## Project Structure

```
cv_agent_pipeline/
├── config/              # YAML configuration files
├── src/
│   ├── agents/          # AI agent implementations
│   ├── providers/       # LLM provider implementations
│   ├── models/          # Pydantic data models
│   ├── pipeline/        # Orchestrator and workflow
│   ├── rendering/       # PDF generation
│   ├── storage/         # ChromaDB vector store
│   └── utils/           # Utilities and helpers
├── templates/           # User experience template
├── output/              # Generated CVs and reports
└── tests/               # Test suite
```

## Roadmap

- [ ] **v0.1.0** (Current): Core pipeline with basic features
- [ ] **v0.2.0**: Cover letter generation agent
- [ ] **v0.3.0**: Resume parsing for existing CVs
- [ ] **v0.4.0**: Web UI (optional Flask/FastAPI frontend)

## Troubleshooting

### Ollama Connection Failed

Ensure Ollama is running:
```bash
ollama serve
```

### PDF Rendering Issues

WeasyPrint requires system dependencies:

**Windows:** GTK3 runtime (bundled with WeasyPrint standalone)
**macOS:** `brew install pango glib libffi`
**Linux:** `apt-get install libpango-1.0-0 libharfbuzz0b libffi-dev`

### Low Quality CVs

- Use a more capable model (e.g., `llama3:70b` or GPT-4)
- Provide more detailed experience information
- Adjust temperature in `config/agents.yaml`

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## Support

For issues and feature requests, please use the GitHub issue tracker.
