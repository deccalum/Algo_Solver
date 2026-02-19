import yaml
import os

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "../config/app.yaml"
            )
            with open(config_path, 'r') as f:
                cls._instance.data = yaml.safe_load(f)
        return cls._instance
    
    def get(self, path: str, default=None):
        """Get nested config value: config.get('solver.defaults.budget_constraint')"""
        keys = path.split('.')
        value = self.data
        for key in keys:
            value = value.get(key, {})
        return value if value != {} else default

# Usage in solver.py:
from config import Config
config = Config()
budget = config.get('solver.defaults.budget_constraint')