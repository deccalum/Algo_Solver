import yaml
import os
from typing import Any, ClassVar, Dict, Optional


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}

class Config:
    _instance: ClassVar[Optional["Config"]] = None
    data: Dict[str, Any]
    
    def __new__(cls) -> "Config":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.data = {}

            config_path = os.path.join(
                os.path.dirname(__file__),
                "../config/app.yaml",
            )
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)

            instance.data = _as_dict(loaded)

            cls._instance = instance
        return cls._instance

    def get(self, path: str, default: Any = None) -> Any:
        """Get nested config value: config.get('solver.defaults.budget_constraint')."""
        value: Any = self.data
        for key in path.split("."):
            if not isinstance(value, dict):
                return default
            value = value.get(key, default)
            if value is default:
                return default
        return default if value == {} else value