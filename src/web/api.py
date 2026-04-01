"""FastAPI web server for CV Agent Pipeline."""

import asyncio
import json
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from src.utils.config_loader import load_config
from src.pipeline.orchestrator import PipelineOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="CV Agent Pipeline API",
    description="Generate tailored CVs using AI agents",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create output directories
OUTPUT_DIR = Path("output/web")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Store for generation tasks
tasks = {}


# ============== Models ==============

class JobInput(BaseModel):
    """Job posting input model."""
    job_url: str
    company_name: Optional[str] = None
    job_title: Optional[str] = None


class CVGenerationRequest(BaseModel):
    """CV generation request model."""
    job_url: str
    experience_text: Optional[str] = None
    max_iterations: int = 3


class CVGenerationResponse(BaseModel):
    """CV generation response model."""
    task_id: str
    status: str
    cv_path: Optional[str] = None
    html_path: Optional[str] = None
    ats_score: Optional[int] = None
    job_fit_score: Optional[int] = None
    error: Optional[str] = None


class TaskStatus(BaseModel):
    """Task status model."""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    current_step: Optional[str] = None
    cv_path: Optional[str] = None
    html_path: Optional[str] = None
    ats_score: Optional[int] = None
    job_fit_score: Optional[int] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


# ============== Background Task ==============

async def generate_cv_background(
    task_id: str,
    job_url: str,
    experience_file: Optional[Path] = None,
):
    """Background task to generate CV."""
    tasks[task_id]["status"] = "running"
    tasks[task_id]["progress"] = 10
    tasks[task_id]["current_step"] = "Initializing pipeline..."
    
    try:
        # Load configuration
        config = load_config(Path("config/config.yaml"))
        
        # Create orchestrator
        orchestrator = PipelineOrchestrator(config)
        
        # Determine experience file
        if experience_file is None:
            experience_file = Path("templates/test_experience.yaml")
        
        tasks[task_id]["progress"] = 30
        tasks[task_id]["current_step"] = "Scraping job posting..."
        
        # Run pipeline
        result = await orchestrator.run(
            job_url=job_url,
            experience_file=experience_file,
        )
        
        # Update task
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100
        tasks[task_id]["current_step"] = "Completed"
        tasks[task_id]["cv_path"] = result.get("cv_path")
        tasks[task_id]["html_path"] = result.get("cv_path", "").replace(".pdf", ".html")
        tasks[task_id]["ats_score"] = result["scores"].get("ats")
        tasks[task_id]["job_fit_score"] = result["scores"].get("job_fit")
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        logger.error(f"Task {task_id} failed: {e}")


# ============== API Endpoints ==============

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web interface."""
    html_path = Path("src/web/index.html")
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    raise HTTPException(status_code=404, detail="Web interface not found")


@app.post("/api/generate", response_model=CVGenerationResponse)
async def generate_cv(
    job_url: str = Form(...),
    experience: Optional[UploadFile] = File(None),
    max_iterations: int = Form(3),
):
    """Generate a tailored CV for a job posting."""
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save uploaded experience file if provided
    experience_file = None
    if experience:
        experience_file = OUTPUT_DIR / f"{task_id}_experience.yaml"
        content = await experience.read()
        experience_file.write_bytes(content)
    
    # Create task
    tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "current_step": "Queued",
        "cv_path": None,
        "html_path": None,
        "ats_score": None,
        "job_fit_score": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    
    # Start background task
    asyncio.create_task(generate_cv_background(
        task_id,
        job_url,
        experience_file,
    ))
    
    return CVGenerationResponse(
        task_id=task_id,
        status="pending",
    )


@app.get("/api/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of a CV generation task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatus(**tasks[task_id])


@app.get("/api/tasks")
async def list_tasks():
    """List all CV generation tasks."""
    return list(tasks.values())


@app.get("/api/cvs")
async def list_cvs():
    """List all generated CVs."""
    cvs_dir = Path("output/cvs")
    if not cvs_dir.exists():
        return []
    
    cvs = []
    for cv_file in cvs_dir.glob("*.html"):
        cvs.append({
            "filename": cv_file.name,
            "path": str(cv_file),
            "created_at": datetime.fromtimestamp(cv_file.stat().st_mtime).isoformat(),
        })
    
    return sorted(cvs, key=lambda x: x["created_at"], reverse=True)


@app.get("/api/cvs/{filename}")
async def get_cv(filename: str):
    """Get a specific CV file."""
    cv_path = Path("output/cvs") / filename
    if not cv_path.exists():
        raise HTTPException(status_code=404, detail="CV not found")
    
    return FileResponse(cv_path)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


# ============== Static Files ==============

# Mount static files directory
static_path = Path("src/web/static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
