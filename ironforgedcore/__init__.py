import importlib.metadata
from pathlib import Path

try:
    __version__ = importlib.metadata.version("ironforgedcore")
except importlib.metadata.PackageNotFoundError:
    _toml_path = Path(__file__).parent.parent / "pyproject.toml"
    if _toml_path.exists():
        import tomllib

        with open(_toml_path, "rb") as _f:
            __version__ = tomllib.load(_f)["project"]["version"]
    else:
        __version__ = "0.0.0+unknown"
