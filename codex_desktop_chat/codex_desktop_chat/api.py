"""Public interface; lazy access preserves real signatures and module identity."""
from importlib import import_module
import json
from pathlib import Path
_EXPORTS=json.loads(Path(__file__).with_name('interface.json').read_text())['python_exports']
__all__=list(_EXPORTS)
def __getattr__(name):
    target=_EXPORTS.get(name)
    if target is None:raise AttributeError(name)
    module,separator,symbol=target.partition(':')
    value=import_module(module)
    return getattr(value,symbol) if separator else value
def __dir__():return sorted(set(globals())|set(__all__))
