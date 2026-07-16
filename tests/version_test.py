import importlib
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch


def _read_pyproject_version() -> str:
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)["project"]["version"]


class TestCorePackageVersion(unittest.TestCase):
    def test_ironforgedcore_version_is_non_empty_string(self):
        import ironforgedcore

        self.assertIsInstance(ironforgedcore.__version__, str)
        self.assertGreater(len(ironforgedcore.__version__), 0)

    def test_ironforgedcore_version_matches_pyproject(self):
        import ironforgedcore

        expected = _read_pyproject_version()
        self.assertEqual(ironforgedcore.__version__, expected)

    def test_ironforgedcore_falls_back_to_pyproject_when_not_installed(self):
        import ironforgedcore

        original = ironforgedcore.__version__
        expected = _read_pyproject_version()
        with patch(
            "importlib.metadata.version",
            side_effect=importlib.metadata.PackageNotFoundError("ironforgedcore"),
        ):
            reloaded = importlib.reload(ironforgedcore)

        try:
            self.assertEqual(reloaded.__version__, expected)
        finally:
            reloaded.__version__ = original


if __name__ == "__main__":
    unittest.main()
