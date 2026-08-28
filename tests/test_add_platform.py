import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from add_platform import add_platform


class AddPlatformTests(unittest.TestCase):
    def test_adds_icon_digest_and_increments_catalog_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            source.write_bytes(b"icon")
            catalog_path = root / "catalog.json"
            catalog_path.write_text(json.dumps({"schema_version": 1, "catalog_version": "1.0.0", "platforms": []}), encoding="utf-8")
            result = add_platform("Example Service", source, catalog_path, root / "platforms")
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

            self.assertEqual(result["catalog_version"], "1.0.1")
            self.assertEqual(catalog["platforms"][0]["icon"], "platforms/example-service.png")
            self.assertEqual(len(catalog["platforms"][0]["sha256"]), 64)

    def test_rejects_duplicate_platform_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            source.write_bytes(b"icon")
            catalog_path = root / "catalog.json"
            catalog_path.write_text(json.dumps({"schema_version": 1, "catalog_version": "1.0.0", "platforms": [{"name": "Example", "icon": "platforms/example.png", "sha256": "a" * 64}]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                add_platform("example", source, catalog_path, root / "platforms")


if __name__ == "__main__":
    unittest.main()
