"""Package initializer for customwidgets."""
#__init__.py
from .info_widget import InfoWidget
from .manifold_widget import ManifoldWidget
from .pump_widget import PumpWidget
from .valve_widget import ValveWidget 

__all__ = [
    "pump_widget",
    "manifold_widget",
    "valve_widget",
    "info_widget"
]
