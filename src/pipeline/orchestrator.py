"""Pipeline orchestrator - Coordinates all agents in the CV generation workflow."""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from loguru import logger

from src.agents.scraper_agent import ScraperAgent
from src.agents.cv_writer_agent import CVWriterAgent
from src.agents.renderer_agent import RendererAgent
from src.agents.ats_scorer_agent import ATSScorerAgent
from src.agents.job_fit_scorer_agent import JobFitScorerAgent
from src.agents.refiner_agent import RefinerAgent
from src.agents.base_agent import AgentConfig

from src.providers.provider_manager import ProviderManager

from src.storage.chroma_store import ChromaStore
from src.models.scores import ScoreReport, ATSScore, JobFitScore
from src.utils.validators import validate_score_thresholds


class PipelineOrchestrator:
    """Orchestrates the CV generation pipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize pipeline orchestrator.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.provider_manager: Optional[ProviderManager] = None
        self.vector_store: Optional[ChromaStore] = None
        self._agents_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all pipeline components.
        
        Returns:
            True if successful
        """
        logger.info("Initializing pipeline orchestrator...")
        
        # Initialize provider manager
        providers_config = self.config.get("providers", {}).get("providers", {})
        fallback_chain = self.config.get("providers", {}).get("fallback_chain", ["ollama"])
        
        self.provider_manager = ProviderManager(providers_config, fallback_chain)
        await self.provider_manager.initialize_all()
        
        # Initialize vector store if enabled
        if self.config.get("pipeline", {}).get("behavior", {}).get("store_to_vector_db", True):
            self.vector_store = ChromaStore(
                persist_directory=".chroma",
                provider_manager=self.provider_manager,
            )
            await self.vector_store.initialize()
        
        self._agents_initialized = True
        logger.info("Pipeline orchestrator initialized")
        return True
    
    async def shutdown(self) -> None:
        """Shutdown pipeline components."""
        if self.provider_manager:
            await self.provider_manager.close_all()
        if self.vector_store:
            await self.vector_store.close()
        self._agents_initialized = False
        logger.info("Pipeline orchestrator shutdown complete")
    
    async def run(
        self,
        job_url: str,
        experience_file: Path,
    ) -> Dict[str, Any]:
        """Run the complete CV generation pipeline.
        
        Args:
            job_url: URL of job posting
            experience_file: Path to user experience YAML
            
        Returns:
            Pipeline result with CV path and scores
        """
        if not self._agents_initialized:
            await self.initialize()
        
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting pipeline run: {run_id}")
        
        result = {
            "run_id": run_id,
            "job_url": job_url,
            "cv_path": None,
            "scores": {"ats": 0, "job_fit": 0},
            "iterations": 0,
        }
        
        try:
            # Load user experience
            import yaml
            with open(experience_file, "r") as f:
                user_experience = yaml.safe_load(f)
            
            # Step 1: Scrape job posting
            logger.info("Step 1: Scraping job posting...")
            scraper = ScraperAgent(self.provider_manager)
            job_data = await scraper.execute(job_url)
            await scraper.close()
            
            # Store job in vector store
            if self.vector_store:
                job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                await self.vector_store.store_job(
                    job_id,
                    job_data.model_dump(),
                )
            
            # Step 2: Generate CV
            logger.info("Step 2: Generating CV...")
            cv_writer = CVWriterAgent(self.provider_manager)
            cv_data = await cv_writer.execute(user_experience, job_data)
            
            # Step 3: Render CV
            logger.info("Step 3: Rendering CV to PDF...")
            output_dir = self.config.get("pipeline", {}).get("paths", {}).get("output_dir", "output")
            cvs_dir = Path(output_dir) / "cvs"
            cvs_dir.mkdir(parents=True, exist_ok=True)
            
            cv_filename = f"cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            cv_path = str(cvs_dir / cv_filename)
            
            renderer = RendererAgent(self.provider_manager)
            render_result = await renderer.execute(cv_data, cv_path)
            cv_path = render_result.get("pdf_path", render_result.get("html_content"))
            result["cv_path"] = cv_path
            html_content = render_result.get("html_content", "")
            
            # Step 4 & 5: Score and refine loop
            logger.info("Step 4: Scoring CV...")
            max_iterations = self.config.get("pipeline", {}).get("behavior", {}).get("max_refinement_iterations", 3)
            thresholds_config = self.config.get("thresholds", {}).get("scoring", {})
            
            ats_agent = ATSScorerAgent(self.provider_manager)
            job_fit_agent = JobFitScorerAgent(self.provider_manager)
            refiner = RefinerAgent(self.provider_manager)
            
            score_report: Optional[ScoreReport] = None
            
            for iteration in range(1, max_iterations + 1):
                result["iterations"] = iteration
                logger.info(f"Refinement iteration {iteration}/{max_iterations}")
                
                # Score CV
                ats_score = await ats_agent.execute(cv_data, html_content)
                job_fit_score = await job_fit_agent.execute(cv_data, job_data)
                
                score_report = ScoreReport(
                    ats=ats_score,
                    job_fit=job_fit_score,
                    cv_version=iteration,
                    job_url=job_url,
                    meets_thresholds=False,
                )
                
                logger.info(f"Iteration {iteration} - ATS: {ats_score.overall_score}, Job Fit: {job_fit_score.overall_score}")
                
                # Check if thresholds met
                meets_thresholds, _ = validate_score_thresholds(
                    ats_score.overall_score,
                    job_fit_score.overall_score,
                    {"scoring": thresholds_config},
                )
                
                score_report.meets_thresholds = meets_thresholds
                
                if meets_thresholds:
                    logger.info("Score thresholds met!")
                    break
                
                # Refine if not last iteration
                if iteration < max_iterations:
                    should_continue = await refiner.should_continue(score_report, iteration)
                    if should_continue:
                        logger.info("Refining CV...")
                        cv_data = await refiner.execute(cv_data, job_data, score_report, iteration)
                        
                        # Re-render
                        render_result = await renderer.execute(cv_data, cv_path)
                        html_content = render_result.get("html_content", "")
            
            # Store final CV
            if self.vector_store and cv_data:
                cv_id = f"cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                await self.vector_store.store_cv(
                    cv_id,
                    cv_data.model_dump(),
                    job_url,
                    {
                        "ats": score_report.ats.model_dump() if score_report else {},
                        "job_fit": score_report.job_fit.model_dump() if score_report else {},
                    },
                )
            
            # Save score report
            if self.config.get("pipeline", {}).get("behavior", {}).get("generate_score_report", True):
                reports_dir = Path(output_dir) / "reports"
                reports_dir.mkdir(parents=True, exist_ok=True)
                
                report_path = reports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_path, "w") as f:
                    json.dump(score_report.model_dump() if score_report else {}, f, indent=2)
            
            # Update result
            if score_report:
                result["scores"] = {
                    "ats": score_report.ats.overall_score,
                    "job_fit": score_report.job_fit.overall_score,
                }
                result["score_report"] = score_report.model_dump()
            
            logger.info(f"Pipeline completed successfully. CV saved to: {cv_path}")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            result["error"] = str(e)
            raise
        
        finally:
            # Cleanup agents
            await self.shutdown()
