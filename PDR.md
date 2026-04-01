# Project Design Report (PDR)
# CV Agent Pipeline

| Field          | Detail                        |
|----------------|-------------------------------|
| Project Name   | CV Agent Pipeline             |
| Version        | 0.1.0                         |
| Status         | Pre-Development               |
| Date           | 2026-04-01                    |
| Author         | —                             |

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Goals and Objectives](#2-goals-and-objectives)
3. [Scope](#3-scope)
4. [System Architecture](#4-system-architecture)
5. [Agent Specifications](#5-agent-specifications)
6. [Data Flow](#6-data-flow)
7. [Model Provider System](#7-model-provider-system)
8. [Tech Stack](#8-tech-stack)
9. [File and Folder Structure](#9-file-and-folder-structure)
10. [Configuration Design](#10-configuration-design)
11. [Risks and Mitigations](#11-risks-and-mitigations)
12. [Constraints and Assumptions](#12-constraints-and-assumptions)
13. [Success Criteria](#13-success-criteria)
14. [Milestones and Roadmap](#14-milestones-and-roadmap)
15. [Dependencies](#15-dependencies)
16. [Open Questions](#16-open-questions)

---

## 1. Project Overview

The CV Agent Pipeline is a locally hosted, multi-agent AI system designed
to automate the creation of tailored, professional CVs. The user provides
their raw experience and a job posting URL. The system then autonomously
writes a CV tailored to that job, renders it as a polished PDF, evaluates
its ATS compatibility, and scores how well it matches the job description.
If scores fall below defined thresholds, the pipeline automatically refines
and regenerates the CV.

The system is model-agnostic, supporting local LLMs via Ollama as well as
external API providers including OpenAI, Anthropic, Groq and Mistral API.
All configuration is driven by YAML files, requiring zero code changes to
switch models or providers.

---

## 2. Goals and Objectives

### Primary Goals

- Automate the end-to-end process of writing and rendering a tailored CV
- Score CVs against ATS compatibility rules before they are submitted
- Score CVs against the actual job description and suggest improvements
- Support both fully offline local inference and external API providers
- Require no code changes to switch models, providers or configuration

### Secondary Goals

- Store past CVs and job descriptions in a vector database for future
  reference and pattern learning
- Build a clean, extensible agent architecture that can accommodate new
  agents such as a cover letter agent in future
- Keep the system easy to run on consumer hardware with a mid-range GPU

---

## 3. Scope

### In Scope

- CV content generation using a local or external LLM
- HTML and CSS based CV rendering to PDF using WeasyPrint
- ATS compatibility scoring and flagging
- Job posting scraping and job fit scoring
- Automatic refinement loop until score thresholds are met
- Multi-provider and multi-model support via YAML configuration
- ChromaDB vector store for past job and CV storage
- Support for Indeed, Glassdoor, Reed, Totaljobs and standard company
  career pages

### Out of Scope (this version)

- A graphical user interface
- Direct LinkedIn job scraping (partial support only)
- Cover letter generation (planned for a future version)
- Automatic job application submission
- Fine-tuning or retraining any models

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CV Agent Pipeline                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │  User    │───▶│ Scraper  │───▶│   CV     │───▶│ Renderer │          │
│  │  Input   │    │  Agent   │    │  Writer  │    │  Agent   │          │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘          │
│       │                                  │                │             │
│       │                                  ▼                ▼             │
│       │                          ┌──────────────────────────┐          │
│       │                          │   Scoring Agents         │          │
│       │                          │  ┌────────┐ ┌─────────┐ │          │
│       │                          │  │  ATS   │ │ Job Fit │ │          │
│       │                          │  │ Scorer │ │ Scorer  │ │          │
│       │                          │  └────────┘ └─────────┘ │          │
│       │                          └──────────────────────────┘          │
│       │                                  │                │             │
│       │                                  ▼                │             │
│       │                          ┌──────────────────┐     │             │
│       └─────────────────────────▶│  Refiner Agent   │─────┘             │
│                                  │  (if scores low) │                   │
│                                  └──────────────────┘                   │
│                                           │                             │
│                                           ▼                             │
│                                  ┌──────────────────┐                   │
│                                  │  ChromaDB Vector │                   │
│                                  │  Store           │                   │
│                                  └──────────────────┘                   │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                      Model Provider Abstraction Layer                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ Ollama  │  │ OpenAI  │  │Anthropic│  │  Groq   │  │ Mistral │       │
│  │ (Local) │  │  API    │  │   API   │  │   API   │  │   API   │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Component Breakdown

| Component | Responsibility |
|-----------|----------------|
| **Orchestrator** | Coordinates agent execution, manages pipeline flow, handles errors |
| **Scraper Agent** | Extracts job title, description, requirements from URLs |
| **CV Writer Agent** | Generates tailored CV content from user data + job description |
| **Renderer Agent** | Converts CV markdown/HTML to polished PDF using WeasyPrint |
| **ATS Scorer Agent** | Evaluates CV against ATS compatibility rules |
| **Job Fit Scorer Agent** | Scores CV relevance against job description |
| **Refiner Agent** | Iterates on CV content based on scoring feedback |
| **Model Provider** | Abstracts LLM access across multiple providers |
| **Vector Store** | Persists CVs and job descriptions for future retrieval |

### 4.3 Pipeline Flow

1. **Input**: User provides raw experience (JSON/YAML) + job posting URL
2. **Scrape**: Scraper Agent fetches and parses job details
3. **Generate**: CV Writer Agent creates tailored CV content
4. **Render**: Renderer Agent produces PDF from HTML/CSS template
5. **Score**: ATS + Job Fit agents evaluate the CV
6. **Refine**: If scores < thresholds, Refiner Agent regenerates
7. **Store**: Final CV + job data saved to ChromaDB
8. **Output**: PDF delivered to user with score report

---

## 5. Agent Specifications

All agents are implemented using LangChain's agent abstractions with custom tools.

### 5.1 Scraper Agent

| Field | Value |
|-------|-------|
| **Purpose** | Extract job details from posting URLs |
| **Input** | Job posting URL |
| **Output** | Structured job data (title, company, description, requirements, location) |
| **Tools** | `httpx` for requests, `BeautifulSoup4` for parsing, `readability-lxml` for content extraction |
| **Supported Sites** | Indeed, Glassdoor, Reed, Totaljobs, standard company career pages |

**Job Data Schema:**
```json
{
  "title": "string",
  "company": "string",
  "location": "string",
  "description": "string",
  "requirements": ["string"],
  "nice_to_have": ["string"],
  "salary": "string (optional)",
  "url": "string"
}
```

### 5.2 CV Writer Agent

| Field | Value |
|-------|-------|
| **Purpose** | Generate tailored CV content |
| **Input** | User raw experience + job data |
| **Output** | CV content in structured format (JSON/Markdown) |
| **LLM** | Configurable via YAML (local or external) |
| **Prompt Strategy** | Few-shot examples + role prompting + constraint-based generation |

**User Experience Schema:**
```json
{
  "personal_info": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "linkedin": "string (optional)",
    "github": "string (optional)"
  },
  "experience": [
    {
      "company": "string",
      "role": "string",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or Present",
      "achievements": ["string"],
      "technologies": ["string"]
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "graduation_date": "YYYY-MM"
    }
  ],
  "skills": ["string"],
  "certifications": ["string (optional)"]
}
```

### 5.3 Renderer Agent

| Field | Value |
|-------|-------|
| **Purpose** | Convert CV content to polished PDF |
| **Input** | CV content (JSON/Markdown) |
| **Output** | PDF file |
| **Tools** | WeasyPrint, Jinja2 templates, CSS styling |
| **Templates** | Professional, clean designs with ATS-friendly formatting |

### 5.4 ATS Scorer Agent

| Field | Value |
|-------|-------|
| **Purpose** | Evaluate CV against ATS compatibility rules |
| **Input** | CV PDF/text |
| **Output** | ATS score (0-100) + list of flags/suggestions |
| **Scoring Criteria** |
| - No images/graphics in critical sections | +10 |
| - Standard section headings used | +10 |
| - No tables for layout | +10 |
| - Standard fonts detected | +10 |
| - Keywords from job description present | +30 |
| - Proper date formatting | +10 |
| - Contact info clearly structured | +10 |
| - File is text-selectable (not scanned) | +10 |

**Threshold**: Minimum 80% required

### 5.5 Job Fit Scorer Agent

| Field | Value |
|-------|-------|
| **Purpose** | Score CV relevance against job description |
| **Input** | CV content + job data |
| **Output** | Job fit score (0-100) + gap analysis |
| **Method** | Semantic similarity + keyword matching via LLM |
| **Scoring Criteria** |
| - Required skills matched | +40 |
| - Experience level alignment | +20 |
| - Industry/domain relevance | +15 |
| - Achievement relevance | +15 |
| - Role progression clarity | +10 |

**Threshold**: Minimum 75% required

### 5.6 Refiner Agent

| Field | Value |
|-------|-------|
| **Purpose** | Iterate on CV based on scoring feedback |
| **Input** | CV content + scores + gap analysis |
| **Output** | Improved CV content |
| **Max Iterations** | 3 (configurable) |
| **Strategy** | Targeted improvements based on lowest-scoring areas |

---

## 6. Data Flow

### 6.1 End-to-End Flow Diagram

```
┌─────────────────┐
│   User Input    │
│  (experience +  │
│   job URL)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Validate &     │────▶│  Parse User     │
│  Load Config    │     │  Experience     │
└─────────────────┘     └─────────────────┘
                                │
                                ▼
┌─────────────────┐     ┌─────────────────┐
│  Store in       │◀────│  Scraper Agent  │
│  ChromaDB       │     │  (fetch job)    │
└─────────────────┘     └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  CV Writer Agent│
                       │  (generate CV)  │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Renderer Agent  │
                       │ (HTML → PDF)    │
                       └─────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  ATS Scorer     │   │  Job Fit Scorer │   │  Store in       │
│  Agent          │   │  Agent          │   │  ChromaDB       │
└────────┬────────┘   └────────┬────────┘   └─────────────────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  Scores >=      │
           │  Thresholds?    │
           └────────┬────────┘
                    │
         ┌──────────┼──────────┐
         │ No                  │ Yes
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│  Refiner Agent  │   │  Output Final   │
│  (iterate)      │   │  CV + Report    │
└─────────────────┘   └─────────────────┘
```

### 6.2 Data Persistence

| Data Type | Storage | Purpose |
|-----------|---------|---------|
| User Experience | Local JSON/YAML | Reuse across sessions |
| Job Descriptions | ChromaDB | Historical reference, pattern learning |
| Generated CVs | ChromaDB + File System | Version history, retrieval |
| Score Reports | File System (JSON) | Audit trail, improvement tracking |
| Configuration | YAML files | System settings, thresholds |

---

## 7. Model Provider System

### 7.1 Provider Abstraction

The system uses a unified interface for all LLM providers, allowing seamless switching via configuration.

```
┌─────────────────────────────────────────┐
│         Agent (LangChain)               │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Model Provider Interface           │
│  - chat()                               │
│  - complete()                           │
│  - embed()                              │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Ollama  │  │ OpenAI  │  │Anthropic│
│ Provider│  │ Provider│  │ Provider│
└─────────┘  └─────────┘  └─────────┘
```

### 7.2 Supported Providers

| Provider | Models | Use Case | Cost |
|----------|--------|----------|------|
| **Ollama** | Llama 3, Mistral, Phi, custom | Local inference (offline) | Free |
| **OpenAI API** | GPT-4, GPT-4o, GPT-3.5-turbo | High-quality generation | Paid |
| **Anthropic API** | Claude 3 (Opus, Sonnet, Haiku) | Long context, nuanced writing | Paid |
| **Groq API** | Llama 3, Mixtral (fast inference) | Low-latency generation | Paid (free tier) |
| **Mistral API** | Mistral Large, Mixtral | Balanced quality/cost | Paid |

### 7.3 Provider Configuration Example

```yaml
# config/providers.yaml
providers:
  ollama:
    enabled: true
    base_url: "http://localhost:11434"
    default_model: "llama3:8b"
    embedding_model: "nomic-embed-text"
    
  openai:
    enabled: false
    api_key_env: "OPENAI_API_KEY"
    default_model: "gpt-4o"
    embedding_model: "text-embedding-3-small"
    
  anthropic:
    enabled: false
    api_key_env: "ANTHROPIC_API_KEY"
    default_model: "claude-3-sonnet-20240229"
    
  groq:
    enabled: false
    api_key_env: "GROQ_API_KEY"
    default_model: "llama3-70b-8192"
    
  mistral:
    enabled: false
    api_key_env: "MISTRAL_API_KEY"
    default_model: "mistral-large-latest"

fallback_chain:
  - ollama
  - groq
  - openai
```

### 7.4 Fallback and Retry Logic

- **Fallback Chain**: If primary provider fails, automatically try next in chain
- **Retry Strategy**: Exponential backoff (1s, 2s, 4s, 8s) with max 4 retries
- **Timeout**: 30 seconds per request (configurable)
- **Rate Limiting**: Respect provider-specified rate limits, queue requests if needed

---

## 8. Tech Stack

### 8.1 Core Technologies

| Category | Technology | Purpose |
|----------|------------|---------|
| **Language** | Python 3.11 | Primary programming language |
| **Agent Framework** | LangChain | Agent orchestration, tool integration, LLM abstraction |
| **Vector Database** | ChromaDB | Store and retrieve CVs, job descriptions, embeddings |
| **PDF Rendering** | WeasyPrint | HTML/CSS to PDF conversion |
| **Web Scraping** | httpx, BeautifulSoup4, readability-lxml | Fetch and parse job postings |
| **Templating** | Jinja2 | CV HTML template rendering |
| **Configuration** | PyYAML | YAML configuration parsing |
| **Validation** | Pydantic | Data validation and settings management |

### 8.2 Supporting Libraries

| Category | Technology | Purpose |
|----------|------------|---------|
| **HTTP Client** | httpx | Async HTTP requests for scraping |
| **HTML Parsing** | BeautifulSoup4, lxml | Parse HTML content |
| **Content Extraction** | readability-lxml | Extract main content from web pages |
| **Embeddings** | sentence-transformers (via ChromaDB) | Generate embeddings for vector search |
| **Logging** | loguru | Structured, colorful logging |
| **CLI** | typer | Command-line interface creation |
| **Testing** | pytest, pytest-asyncio | Unit and integration tests |

### 8.3 Local LLM Stack (Optional)

| Technology | Purpose |
|------------|---------|
| **Ollama** | Local LLM runtime |
| **Llama 3 8B/70B** | Primary local model for generation |
| **Mistral 7B** | Alternative local model |
| **Nomic Embed Text** | Local embeddings for ChromaDB |

### 8.4 Development Tools

| Category | Technology |
|----------|------------|
| **Package Management** | uv or pip |
| **Virtual Environment** | venv or conda |
| **Code Formatting** | ruff, black |
| **Type Checking** | mypy |
| **Version Control** | git |

---

## 9. File and Folder Structure

```
cv_agent_pipeline/
├── config/
│   ├── config.yaml           # Main pipeline configuration
│   ├── providers.yaml        # LLM provider settings
│   ├── agents.yaml           # Agent-specific prompts and parameters
│   └── thresholds.yaml       # ATS and job fit score thresholds
│
├── src/
│   ├── __init__.py
│   ├── main.py               # Entry point, CLI commands
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py     # Base agent class with LangChain integration
│   │   ├── scraper_agent.py  # Job posting scraper
│   │   ├── cv_writer_agent.py # CV content generator
│   │   ├── renderer_agent.py # PDF renderer
│   │   ├── ats_scorer_agent.py # ATS compatibility scorer
│   │   ├── job_fit_scorer_agent.py # Job fit scorer
│   │   └── refiner_agent.py  # CV refinement agent
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base_provider.py  # Abstract provider interface
│   │   ├── ollama_provider.py # Ollama implementation
│   │   ├── openai_provider.py # OpenAI implementation
│   │   ├── anthropic_provider.py # Anthropic implementation
│   │   ├── groq_provider.py  # Groq implementation
│   │   └── mistral_provider.py # Mistral implementation
│   │
│   ├── rendering/
│   │   ├── __init__.py
│   │   ├── templates/
│   │   │   ├── cv_template.html      # Main CV HTML template
│   │   │   └── styles/
│   │   │       └── cv_styles.css     # CV styling
│   │   └── pdf_generator.py          # WeasyPrint integration
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── chroma_store.py   # ChromaDB wrapper
│   │   └── schemas.py        # Data schemas for storage
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py   # Main pipeline coordinator
│   │   └── workflow.py       # Workflow definitions
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py            # Job data models
│   │   ├── cv.py             # CV data models
│   │   └── scores.py         # Score report models
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config_loader.py  # Configuration loading utilities
│       ├── logger.py         # Logging setup
│       └── validators.py     # Input validation
│
├── templates/
│   └── user_experience.yaml  # Template for user to fill in their experience
│
├── output/
│   ├── cvs/                  # Generated CV PDFs
│   ├── reports/              # Score reports (JSON)
│   └── logs/                 # Application logs
│
├── tests/
│   ├── __init__.py
│   ├── test_scraper_agent.py
│   ├── test_cv_writer_agent.py
│   ├── test_renderer_agent.py
│   ├── test_ats_scorer_agent.py
│   ├── test_job_fit_scorer_agent.py
│   ├── test_refiner_agent.py
│   ├── test_providers.py
│   └── test_pipeline.py
│
├── .env.example              # Example environment variables
├── .gitignore
├── pyproject.toml            # Project metadata and dependencies
├── requirements.txt          # Pinned dependencies (optional)
└── README.md                 # Project documentation
```

---

## 10. Configuration Design

### 10.1 Configuration Files Overview

| File | Purpose |
|------|---------|
| `config.yaml` | Main pipeline settings, paths, general behavior |
| `providers.yaml` | LLM provider credentials, models, fallback chain |
| `agents.yaml` | Agent-specific prompts, parameters, iteration limits |
| `thresholds.yaml` | Minimum scores required, refinement triggers |

### 10.2 config.yaml Example

```yaml
# config/config.yaml
pipeline:
  name: "CV Agent Pipeline"
  version: "0.1.0"
  
  # Input/Output paths
  paths:
    user_experience: "templates/user_experience.yaml"
    output_dir: "output"
    cvs_dir: "output/cvs"
    reports_dir: "output/reports"
    logs_dir: "output/logs"
    
  # Pipeline behavior
  behavior:
    max_refinement_iterations: 3
    store_to_vector_db: true
    generate_score_report: true
    
  # Scraping settings
  scraping:
    user_agent: "Mozilla/5.0 (compatible; CVAgentBot/1.0)"
    request_timeout: 10
    retry_count: 3
    
  # Rendering settings
  rendering:
    page_size: "A4"
    margin_top: "20mm"
    margin_bottom: "20mm"
    margin_left: "15mm"
    margin_right: "15mm"
    
logging:
  level: "INFO"
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
  file: "output/logs/pipeline.log"
```

### 10.3 agents.yaml Example

```yaml
# config/agents.yaml
cv_writer:
  system_prompt: |
    You are an expert CV writer with 15+ years of experience.
    Your task is to create tailored, professional CVs that highlight
    the candidate's most relevant experience for each job.
    
    Guidelines:
    - Use action verbs and quantify achievements
    - Keep bullet points concise (1-2 lines each)
    - Prioritize relevance to the job description
    - Maintain a professional, confident tone
    
  temperature: 0.7
  max_tokens: 2000
  
scraper:
  extract_full_page: true
  clean_html: true
  
ats_scorer:
  check_sections: true
  check_keywords: true
  check_formatting: true
  
job_fit_scorer:
  use_semantic_similarity: true
  keyword_weight: 0.4
  semantic_weight: 0.6
  
refiner:
  focus_on_lowest_scores: true
  preserve_original_structure: true
```

### 10.4 thresholds.yaml Example

```yaml
# config/thresholds.yaml
scoring:
  ats:
    minimum_score: 80
    critical_checks:
      - "contact_info_present"
      - "standard_headings"
      - "no_images_in_content"
      - "text_selectable"
      
  job_fit:
    minimum_score: 75
    required_skill_match_percentage: 60
    
refinement:
  trigger_below_threshold: true
  max_iterations: 3
  improvement_target: 10  # Aim for 10% improvement per iteration
```

### 10.5 Environment Variables

```bash
# .env.example
# API Keys (uncomment and set for providers you use)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
MISTRAL_API_KEY=...

# Ollama (no key needed, runs locally)
OLLAMA_BASE_URL=http://localhost:11434

# ChromaDB (optional, for remote instances)
CHROMA_DB_HOST=localhost
CHROMA_DB_PORT=8000
```

---

## 11. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Job site scraping blocks** | High | Medium | Use respectful delays, rotate user agents, implement rate limiting, support manual job description input as fallback |
| **Local LLM quality insufficient** | High | Medium | Support external providers as fallback, recommend larger local models (Llama 3 70B), provide model comparison guidance |
| **PDF rendering inconsistencies** | Medium | Low | Test templates across platforms, use WeasyPrint's well-documented CSS support, provide template customization |
| **ATS scoring inaccuracies** | High | Medium | Validate against known ATS systems, allow manual score override, continuously improve scoring rules based on feedback |
| **API rate limits exceeded** | Medium | Medium | Implement exponential backoff, respect rate limits, queue requests, provide usage warnings |
| **Vector store performance degradation** | Low | Low | Implement collection cleanup, limit stored embeddings per user, use efficient similarity search |
| **Configuration complexity** | Medium | High | Provide sensible defaults, include example configs, add config validation with clear error messages |
| **Privacy concerns with external APIs** | Medium | Low | Default to local inference, clearly document data sent to external providers, support offline-only mode |

---

## 12. Constraints and Assumptions

### 12.1 Constraints

| Constraint | Description |
|------------|-------------|
| **Hardware** | Designed for consumer hardware with mid-range GPU (8GB+ VRAM recommended for local LLMs) |
| **Memory** | Local LLMs require 8-16GB RAM depending on model size |
| **Storage** | ~10GB for local models, ~1GB for application and dependencies |
| **Network** | External providers require internet; local mode works offline after model download |
| **Job Sites** | Some job sites may have aggressive anti-bot measures that limit scraping reliability |

### 12.2 Assumptions

| Assumption | Description |
|------------|-------------|
| **User Input** | User provides structured, honest information about their experience |
| **Job Posting Quality** | Job postings contain sufficient detail for meaningful CV tailoring |
| **Model Availability** | Specified models are available from chosen providers |
| **PDF Viewer** | User has a PDF viewer to open generated CVs |
| **Technical Comfort** | User is comfortable with CLI tools and basic configuration |
| **Language** | Primary support for English CVs; other languages depend on model capabilities |

---

## 13. Success Criteria

### 13.1 Functional Success

| Criterion | Target |
|-----------|--------|
| **End-to-End Time** | CV generated within 5 minutes (external API) or 10 minutes (local LLM) |
| **ATS Score** | Average ATS score > 80% across generated CVs |
| **Job Fit Score** | Average job fit score > 75% across generated CVs |
| **Refinement Success** | 90% of CVs meet thresholds within 2 refinement iterations |
| **Provider Switching** | Zero code changes required to switch providers |

### 13.2 Quality Success

| Criterion | Target |
|-----------|--------|
| **CV Quality** | Generated CVs pass manual review for professionalism and accuracy |
| **PDF Quality** | PDFs render correctly across major viewers (Adobe, Chrome, Preview) |
| **Error Handling** | Graceful degradation when providers fail, clear error messages |
| **Test Coverage** | > 80% unit test coverage for core agent logic |

### 13.3 Usability Success

| Criterion | Target |
|-----------|--------|
| **Setup Time** | New users can run first CV within 15 minutes of cloning |
| **Configuration** | Common tasks (switch model, adjust thresholds) require only YAML edits |
| **Documentation** | README provides clear setup and usage instructions |

---

## 14. Milestones and Roadmap

### Phase 1: Foundation (M1)
**Duration**: 2 weeks

- [ ] Project scaffolding and directory structure
- [ ] Configuration system (YAML loading, validation)
- [ ] Base provider interface with Ollama support
- [ ] Scraper Agent (basic job extraction)
- [ ] CV Writer Agent (basic generation)
- [ ] Renderer Agent (simple PDF output)
- [ ] CLI entry point

**Deliverable**: Working pipeline that generates a basic CV from user input + job URL

---

### Phase 2: Multi-Provider Support (M2)
**Duration**: 1 week

- [ ] OpenAI provider implementation
- [ ] Anthropic provider implementation
- [ ] Groq provider implementation
- [ ] Mistral provider implementation
- [ ] Fallback chain logic
- [ ] Provider selection via config

**Deliverable**: Ability to switch between providers via YAML config

---

### Phase 3: Scoring and Refinement (M3)
**Duration**: 2 weeks

- [ ] ATS Scorer Agent implementation
- [ ] Job Fit Scorer Agent implementation
- [ ] Refiner Agent implementation
- [ ] Refinement loop orchestration
- [ ] Score report generation

**Deliverable**: Automatic CV refinement until quality thresholds met

---

### Phase 4: Vector Store Integration (M4)
**Duration**: 1 week

- [ ] ChromaDB integration
- [ ] CV and job description storage
- [ ] Basic retrieval for pattern learning
- [ ] Historical CV lookup

**Deliverable**: Persistent storage of CVs and jobs with semantic search

---

### Phase 5: Polish and Documentation (M5)
**Duration**: 1 week

- [ ] Comprehensive README
- [ ] Example configurations
- [ ] User experience template
- [ ] Test suite completion
- [ ] Error handling improvements
- [ ] Performance optimization

**Deliverable**: Production-ready v0.1.0 release

---

### Future Versions (Post-v0.1.0)

| Feature | Priority | Notes |
|---------|----------|-------|
| Cover Letter Agent | High | Similar pipeline for cover letters |
| LinkedIn Job Support | Medium | Workaround for LinkedIn scraping restrictions |
| Resume Parsing | Medium | Parse existing CVs to populate user experience |
| Web UI | Low | Optional Flask/FastAPI frontend |
| Fine-tuned Models | Low | Custom fine-tuning for CV-specific tasks |

---

## 15. Dependencies

### 15.1 Core Python Dependencies

```python
# pyproject.toml dependencies (approximate)

[project]
requires-python = ">=3.11"

[project.optional-dependencies]
core = [
    "langchain>=0.1.0",
    "langchain-community>=0.0.10",
    "chromadb>=0.4.22",
    "weasyprint>=60.0",
    "jinja2>=3.1.3",
    "pyyaml>=6.0.1",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
]

scraping = [
    "httpx>=0.26.0",
    "beautifulsoup4>=4.12.3",
    "lxml>=5.1.0",
    "readability-lxml>=0.8.1",
]

providers = [
    "openai>=1.10.0",
    "anthropic>=0.8.0",
    "groq>=0.4.0",
]

utils = [
    "loguru>=0.7.2",
    "typer>=0.9.0",
]

dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.4",
    "ruff>=0.1.13",
    "black>=24.1.0",
    "mypy>=1.8.0",
]
```

### 15.2 System Dependencies (for WeasyPrint)

| OS | Dependencies |
|----|--------------|
| **Windows** | GTK3 runtime (bundled with WeasyPrint standalone) |
| **macOS** | `brew install pango glib libffi` |
| **Linux (Debian/Ubuntu)** | `apt-get install libpango-1.0-0 libharfbuzz0b libffi-dev` |
| **Linux (Fedora)** | `dnf install pango glib libffi` |

### 15.3 Optional: Ollama Setup

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Install Ollama (Windows)
# Download from https://ollama.com/download

# Pull recommended models
ollama pull llama3:8b
ollama pull nomic-embed-text
```

---

## 16. Open Questions

| Question | Options | Decision Needed By |
|----------|---------|-------------------|
| **Which local LLM to recommend as default?** | Llama 3 8B (faster), Llama 3 70B (better quality), Mistral 7B (balanced) | M1 |
| **Should we support resume parsing for existing CVs?** | Yes (add parser), No (manual input only) | M2 |
| **Rate limiting strategy for external APIs?** | Fixed delay, token bucket, provider-specific limits | M2 |
| **How to handle multi-page job descriptions?** | Truncate to N tokens, summarization first, full extraction | M1 |
| **CV template variety?** | Single template v1, multiple templates v1, community templates later | M1 |
| **Should scoring agents use same LLM as writer?** | Same (simpler), Different (specialized models for scoring) | M3 |
| **Vector store: embedded or standalone ChromaDB?** | Embedded (simpler), Standalone server (scalable) | M4 |
| **Support for non-English CVs?** | English-only v1, Multi-language if model supports | M1 |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **ATS** | Applicant Tracking System - software used by employers to filter CVs |
| **LLM** | Large Language Model - AI model for text generation |
| **Embedding** | Vector representation of text for semantic search |
| **ChromaDB** | Vector database for storing and searching embeddings |
| **WeasyPrint** | Python library for converting HTML/CSS to PDF |
| **LangChain** | Framework for building LLM-powered applications |
| **Ollama** | Local LLM runtime for running models on consumer hardware |
| **Job Fit** | Measure of how well a CV matches the job description |
| **Provider** | LLM service (local or API) that powers the agents |
| **Refinement Loop** | Iterative process of scoring and improving CV content |
| **Vector Store** | Database optimized for similarity search on embeddings |

---

## Appendix B: Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-04-01 | — | Initial PDR draft with complete sections 1-16 |

