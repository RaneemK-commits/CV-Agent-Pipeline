"""Configuration loader for YAML files."""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML files.
    
    Args:
        config_path: Optional path to main config file
        
    Returns:
        Merged configuration dictionary
    """
    if config_path is None:
        # Default paths
        config_path = Path("config/config.yaml")
    
    config_dir = config_path.parent
    
    # Load main config
    config = _load_yaml_file(config_path)
    
    # Load providers config
    providers_path = config_dir / "providers.yaml"
    if providers_path.exists():
        config["providers"] = _load_yaml_file(providers_path)
    
    # Load agents config
    agents_path = config_dir / "agents.yaml"
    if agents_path.exists():
        config["agents"] = _load_yaml_file(agents_path)
    
    # Load thresholds config
    thresholds_path = config_dir / "thresholds.yaml"
    if thresholds_path.exists():
        config["thresholds"] = _load_yaml_file(thresholds_path)
    
    logger.info(f"Loaded configuration from {config_path.parent}")
    return config


def _load_yaml_file(path: Path) -> Dict[str, Any]:
    """Load a single YAML file.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Parsed YAML content
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
        logger.debug(f"Loaded config: {path}")
        return content or {}
    except Exception as e:
        logger.error(f"Failed to load config {path}: {e}")
        return {}


def save_config(config: Dict[str, Any], path: Path) -> None:
    """Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary
        path: Path to save to
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Saved configuration to {path}")


def get_nested(config: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Get nested configuration value.
    
    Args:
        config: Configuration dictionary
        *keys: Keys to traverse
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current
