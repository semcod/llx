"""Tests for project type detection."""

import pytest
from pathlib import Path
import tempfile
import os
import sys

# Add llx to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from llx.detection import ProjectTypeDetector


class TestProjectTypeDetector:
    """Test project type detection functionality."""
    
    def setup_method(self):
        """Set up test detector."""
        self.detector = ProjectTypeDetector()
    
    def test_detect_api_from_path(self):
        """Test API detection from directory name."""
        assert self.detector.detect_from_path(Path("my-api")) == "api"
        assert self.detector.detect_from_path(Path("rest-service")) == "api"
        assert self.detector.detect_from_path(Path("api-test")) == "api"
        assert self.detector.detect_from_path(Path("random-name")) is None
    
    def test_detect_webapp_from_path(self):
        """Test webapp detection from directory name."""
        assert self.detector.detect_from_path(Path("my-app")) == "webapp"
        assert self.detector.detect_from_path(Path("webapp-test")) == "webapp"
        assert self.detector.detect_from_path(Path("react-dashboard")) == "webapp"
    
    def test_detect_cli_from_path(self):
        """Test CLI detection from directory name."""
        assert self.detector.detect_from_path(Path("my-cli")) == "cli"
        assert self.detector.detect_from_path(Path("tool-backup")) == "cli"
        assert self.detector.detect_from_path(Path("cli-processor")) == "cli"
    
    def test_detect_from_files_package_json(self):
        """Test webapp detection from package.json."""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp).joinpath("package.json").write_text('{"name": "test"}')
            assert self.detector.detect_from_files(Path(tmp)) == "webapp"
    
    def test_detect_from_files_setup_py_click(self):
        """Test CLI detection from setup.py with click."""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp).joinpath("setup.py").write_text("from click import ClickGroup")
            assert self.detector.detect_from_files(Path(tmp)) == "cli"
    
    def test_detect_from_files_requirements_txt_fastapi(self):
        """Test API detection from requirements.txt with fastapi."""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp).joinpath("requirements.txt").write_text("fastapi\nuvicorn")
            assert self.detector.detect_from_files(Path(tmp)) == "api"
    
    def test_detect_from_files_model_files(self):
        """Test ML detection from model files."""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp).joinpath("model.pkl").touch()
            assert self.detector.detect_from_files(Path(tmp)) == "ml"
    
    def test_detect_from_files_data_directory(self):
        """Test data detection from data directory."""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp).joinpath("data").mkdir()
            assert self.detector.detect_from_files(Path(tmp)) == "data"
    
    def test_detect_from_config(self):
        """Test detection from .llx-project-type file."""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp).joinpath(".llx-project-type").write_text("webapp")
            assert self.detector.detect_from_config(Path(tmp)) == "webapp"
    
    def test_detect_priority(self):
        """Test detection priority: config > files > path > default."""
        with tempfile.TemporaryDirectory() as tmp:
            # Create directory that matches api pattern
            test_path = Path(tmp) / "my-api"
            test_path.mkdir()
            
            # Add package.json (should override api detection)
            test_path.joinpath("package.json").write_text("{}")
            assert self.detector.detect(test_path) == "webapp"
            
            # Add .llx-project-type (should override everything)
            test_path.joinpath(".llx-project-type").write_text("cli")
            assert self.detector.detect(test_path) == "cli"
    
    def test_get_project_config(self):
        """Test getting project configuration."""
        config = self.detector.get_project_config("api")
        assert config["default_sprints"] == 8
        assert config["default_framework"] == "fastapi"
        assert "fastapi" in config["supported_frameworks"]
    
    def test_get_all_types(self):
        """Test getting all project types."""
        types = self.detector.get_all_types()
        assert "api" in types
        assert "webapp" in types
        assert "cli" in types
        assert "data" in types
        assert "ml" in types
    
    def test_detect_default_to_api(self):
        """Test that detection defaults to API."""
        with tempfile.TemporaryDirectory() as tmp:
            test_path = Path(tmp) / "random-directory"
            test_path.mkdir()
            assert self.detector.detect(test_path) == "api"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
