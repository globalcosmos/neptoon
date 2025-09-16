_LAZY_IMPORTS = {
    "CRNSDataHub": (
        "neptoon.hub",
        "CRNSDataHub",
    ),
}

_ATTR_CACHE = {}


def __getattr__(name: str):
    """Load functions and classes on-demand when first accessed."""

    # Check cache first
    if name in _ATTR_CACHE:
        return _ATTR_CACHE[name]

    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]

        from importlib import import_module

        module = import_module(module_path)
        attr = getattr(module, attr_name)

        # Cache it for future access
        _ATTR_CACHE[name] = attr
        globals()[name] = attr

        return attr

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__():
    """Show all available attributes including lazy ones."""
    regular_attrs = [
        name for name in globals().keys() if not name.startswith("_")
    ]
    lazy_attrs = list(_LAZY_IMPORTS.keys())
    return sorted(set(regular_attrs + lazy_attrs))


__all__ = list(_LAZY_IMPORTS.keys())


VERSION = "v0.13.0"

__version__ = VERSION
