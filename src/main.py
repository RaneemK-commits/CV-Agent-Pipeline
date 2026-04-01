"""Main entry point for the CV Agent Pipeline CLI."""

import typer
from pathlib import Path
from typing import Optional

from loguru import logger

from src.utils.config_loader import load_config
from src.pipeline.orchestrator import PipelineOrchestrator

app = typer.Typer(
    name="cv-agent",
    help="CV Agent Pipeline - Generate tailored CVs using AI agents",
    add_completion=False,
)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Configure logging for the application."""
    logger.remove()
    logger.add(
        lambda msg: typer.echo(msg, err=True),
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logger.add(log_file, level=log_level, rotation="10 MB")


@app.command()
def generate(
    job_url: str = typer.Argument(..., help="URL of the job posting"),
    experience_file: Optional[Path] = typer.Option(
        None,
        "--experience",
        "-e",
        help="Path to your experience YAML file (default: from config)",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file (default: config/config.yaml)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for generated CV (default: from config)",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level",
    ),
) -> None:
    """Generate a tailored CV for a job posting."""
    setup_logging(log_level)
    
    try:
        # Load configuration
        config = load_config(config_file) if config_file else load_config()
        
        # Override output dir if specified
        if output_dir:
            config["pipeline"]["paths"]["output_dir"] = str(output_dir)
        
        # Determine experience file
        exp_file = experience_file or Path(config["pipeline"]["paths"]["user_experience"])
        
        if not exp_file.exists():
            logger.error(f"Experience file not found: {exp_file}")
            raise typer.Exit(code=1)
        
        # Initialize and run pipeline
        orchestrator = PipelineOrchestrator(config)
        result = orchestrator.run(
            job_url=job_url,
            experience_file=exp_file,
        )
        
        logger.success(f"CV generated successfully: {result['cv_path']}")
        logger.info(f"ATS Score: {result['scores']['ats']}/100")
        logger.info(f"Job Fit Score: {result['scores']['job_fit']}/100")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise typer.Exit(code=1)


@app.command()
def init(
    output_dir: Path = typer.Argument(
        ".",
        help="Directory to initialize",
    ),
) -> None:
    """Initialize a new CV Agent project with template files."""
    from pathlib import Path
    import shutil
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Copy template experience file
    template_src = Path(__file__).parent.parent / "templates" / "user_experience.yaml"
    template_dst = output_path / "user_experience.yaml"
    
    if template_src.exists():
        shutil.copy(template_src, template_dst)
        typer.echo(f"✓ Created user_experience.yaml template")
    
    typer.echo(f"\nNext steps:")
    typer.echo(f"1. Edit user_experience.yaml with your information")
    typer.echo(f"2. Run: cv-agent generate <job-url> --experience user_experience.yaml")


@app.command()
def version() -> None:
    """Show version information."""
    from src import __version__
    typer.echo(f"CV Agent Pipeline v{__version__}")


if __name__ == "__main__":
    app()
