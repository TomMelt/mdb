from typing import Dict, Type
from mdb.base import DebugBackend

backends: Dict[str, Type[DebugBackend]] = {}

def register_backends():
    # Import plugins AFTER base class is defined
    from .plugins import vgdb, gdb, lldb
    
    for cls in DebugBackend.__subclasses__():
        instance = cls()
        backends[instance.name] = cls