"""Workflow definitions for the CV pipeline."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStep(str, Enum):
    """Pipeline execution steps."""
    
    INITIALIZE = "initialize"
    SCRAPE_JOB = "scrape_job"
    GENERATE_CV = "generate_cv"
    RENDER_CV = "render_cv"
    SCORE_ATS = "score_ats"
    SCORE_JOB_FIT = "score_job_fit"
    REFINE = "refine"
    STORE = "store"
    COMPLETE = "complete"


class StepResult(BaseModel):
    """Result of a pipeline step."""
    
    step: PipelineStep = Field(..., description="Step name")
    status: PipelineStatus = Field(..., description="Step status")
    started_at: datetime = Field(default_factory=datetime.now, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    error: Optional[str] = Field(None, description="Error message if failed")
    data: Optional[Dict[str, Any]] = Field(None, description="Step output data")


class WorkflowState(BaseModel):
    """State machine for workflow execution."""
    
    run_id: str = Field(..., description="Unique run identifier")
    status: PipelineStatus = Field(default=PipelineStatus.PENDING, description="Current status")
    current_step: Optional[PipelineStep] = Field(None, description="Current step")
    completed_steps: List[PipelineStep] = Field(default_factory=list, description="Completed steps")
    step_results: List[StepResult] = Field(default_factory=list, description="All step results")
    started_at: datetime = Field(default_factory=datetime.now, description="Workflow start time")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion time")
    
    def start_step(self, step: PipelineStep) -> StepResult:
        """Mark a step as started.
        
        Args:
            step: Step to start
            
        Returns:
            Step result
        """
        self.current_step = step
        result = StepResult(step=step, status=PipelineStatus.RUNNING)
        self.step_results.append(result)
        return result
    
    def complete_step(self, step: PipelineStep, data: Optional[Dict[str, Any]] = None) -> None:
        """Mark a step as completed.
        
        Args:
            step: Step to complete
            data: Optional step output data
        """
        self.current_step = None
        self.completed_steps.append(step)
        
        for result in reversed(self.step_results):
            if result.step == step and result.status == PipelineStatus.RUNNING:
                result.status = PipelineStatus.COMPLETED
                result.completed_at = datetime.now()
                result.data = data
                break
    
    def fail_step(self, step: PipelineStep, error: str) -> None:
        """Mark a step as failed.
        
        Args:
            step: Step to fail
            error: Error message
        """
        self.current_step = None
        self.status = PipelineStatus.FAILED
        self.completed_at = datetime.now()
        
        for result in reversed(self.step_results):
            if result.step == step and result.status == PipelineStatus.RUNNING:
                result.status = PipelineStatus.FAILED
                result.error = error
                result.completed_at = datetime.now()
                break
    
    def can_proceed_to(self, step: PipelineStep) -> bool:
        """Check if workflow can proceed to a step.
        
        Args:
            step: Step to check
            
        Returns:
            True if can proceed
        """
        # Define step dependencies
        dependencies = {
            PipelineStep.SCRAPE_JOB: [PipelineStep.INITIALIZE],
            PipelineStep.GENERATE_CV: [PipelineStep.SCRAPE_JOB],
            PipelineStep.RENDER_CV: [PipelineStep.GENERATE_CV],
            PipelineStep.SCORE_ATS: [PipelineStep.RENDER_CV],
            PipelineStep.SCORE_JOB_FIT: [PipelineStep.RENDER_CV],
            PipelineStep.REFINE: [PipelineStep.SCORE_ATS, PipelineStep.SCORE_JOB_FIT],
            PipelineStep.STORE: [PipelineStep.SCORE_ATS, PipelineStep.SCORE_JOB_FIT],
        }
        
        required = dependencies.get(step, [])
        return all(s in self.completed_steps for s in required)


class WorkflowConfig(BaseModel):
    """Configuration for workflow execution."""
    
    max_refinement_iterations: int = Field(default=3, description="Max refinement iterations")
    ats_threshold: int = Field(default=80, description="Minimum ATS score")
    job_fit_threshold: int = Field(default=75, description="Minimum job fit score")
    store_to_vector_db: bool = Field(default=True, description="Store to vector DB")
    generate_score_report: bool = Field(default=True, description="Generate score report")
    stop_on_low_score: bool = Field(default=False, description="Stop if scores too low")
    min_score_threshold: int = Field(default=50, description="Minimum score to continue")
