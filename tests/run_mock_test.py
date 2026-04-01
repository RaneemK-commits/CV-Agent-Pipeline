"""Mock test script for CV pipeline."""

import asyncio
from pathlib import Path
from loguru import logger

from src.utils.config_loader import load_config
from src.pipeline.orchestrator import PipelineOrchestrator


async def run_mock_test():
    """Run a mock CV generation test."""
    logger.info("=" * 60)
    logger.info("CV Agent Pipeline - Mock Test")
    logger.info("=" * 60)
    
    # Load configuration
    config = load_config(Path("config/config.yaml"))
    
    # Override to use mock provider
    config["providers"]["providers"]["mock"]["enabled"] = True
    config["providers"]["fallback_chain"] = ["mock"]
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(config)
    
    try:
        # Run pipeline with mock data
        result = await orchestrator.run(
            job_url="https://example.com/jobs/test-123",
            experience_file=Path("templates/test_experience.yaml"),
        )
        
        logger.info("=" * 60)
        logger.info("Mock Test Results")
        logger.info("=" * 60)
        logger.info(f"Run ID: {result['run_id']}")
        logger.info(f"CV Path: {result.get('cv_path', 'N/A')}")
        logger.info(f"Iterations: {result.get('iterations', 0)}")
        logger.info(f"ATS Score: {result['scores'].get('ats', 0)}")
        logger.info(f"Job Fit Score: {result['scores'].get('job_fit', 0)}")
        logger.info("=" * 60)
        logger.info("✅ Mock test completed successfully!")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Mock test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(run_mock_test())
