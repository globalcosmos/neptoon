from .hub import CRNSDataHub


from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("neptoon")
except PackageNotFoundError:
    __version__ = "unknown"
