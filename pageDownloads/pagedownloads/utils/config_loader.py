import yaml
from pathlib import Path
from typing import Any, Dict


class ConfigLoader:
    """Load and validate YAML configuration."""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if self._config is not None:
            return self._config

        if config_path is None:
            # Search for config.yaml in: current dir, script dir, project root
            search_paths = [
                Path.cwd() / "config.yaml",
                Path(__file__).parent.parent / "config.yaml",
            ]

            for path in search_paths:
                if path.exists():
                    config_path = str(path)
                    break

            if config_path is None:
                raise FileNotFoundError(
                    "config.yaml not found. Please create one in the project root."
                )

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        return self._config

    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """Get configuration value by section and optional key."""
        if self._config is None:
            self.load()

        section_data = self._config.get(section, {})

        if key is None:
            return section_data

        # Support nested keys like "selenium.wait_time"
        keys = key.split('.')
        value = section_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default

        return value if value is not None else default


# Singleton instance
config = ConfigLoader()
