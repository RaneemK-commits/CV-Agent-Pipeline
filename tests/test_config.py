"""Tests for configuration loader."""

import pytest
import yaml
from pathlib import Path
from src.utils.config_loader import load_config, get_nested, save_config


class TestConfigLoader:
    """Tests for configuration loading."""
    
    def test_load_default_config(self, tmp_path):
        """Test loading default configuration."""
        # Create temp config files
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        config_file = config_dir / "config.yaml"
        config_file.write_text("""
pipeline:
  name: "Test Pipeline"
  version: "0.1.0"
""")
        
        config = load_config(config_file)
        assert config["pipeline"]["name"] == "Test Pipeline"
    
    def test_get_nested_value(self):
        """Test getting nested configuration values."""
        config = {
            "pipeline": {
                "behavior": {
                    "max_iterations": 3
                }
            }
        }
        
        value = get_nested(config, "pipeline", "behavior", "max_iterations")
        assert value == 3
    
    def test_get_nested_default(self):
        """Test getting nested value with default."""
        config = {"pipeline": {}}
        
        value = get_nested(config, "pipeline", "missing", "key", default=5)
        assert value == 5
    
    def test_save_config(self, tmp_path):
        """Test saving configuration."""
        config = {"test": "value", "number": 42}
        output_path = tmp_path / "output.yaml"
        
        save_config(config, output_path)
        
        # Verify saved content
        with open(output_path) as f:
            saved = yaml.safe_load(f)
        
        assert saved["test"] == "value"
        assert saved["number"] == 42
