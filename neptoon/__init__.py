import sys
from types import ModuleType

# Create fake module with the classes SaQC
fake_gui = ModuleType("saqc.lib.selectionGUI")
fake_gui.MplScroller = type("MplScroller", (), {})
fake_gui.SelectionOverlay = type("SelectionOverlay", (), {})

sys.modules["saqc.lib.selectionGUI"] = fake_gui


from .hub import CRNSDataHub


VERSION = "v0.11.2"

__version__ = VERSION
