# src/mdb/backend.py
from .base import DebugBackend  # Import from base instead of plugins
from .registry import backends  # Import the registry

# Initialize backends when module loads
from .registry import register_backends


register_backends()