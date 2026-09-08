import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from add_platform import add_platform, replace_platform_icons


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

    def test_replaces_multiple_icons_and_increments_catalog_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            platforms_dir = root / "platforms"
            platforms_dir.mkdir()
            (platforms_dir / "one.png").write_bytes(b"old-one")
            (platforms_dir / "two.png").write_bytes(b"old-two")
            source_one = root / "source-one.png"
            source_two = root / "source-two.png"
            source_one.write_bytes(b"new-one")
            source_two.write_bytes(b"new-two")
            catalog_path = root / "catalog.json"
            catalog_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "catalog_version": "1.0.5",
                        "platforms": [
                            {"name": "One", "icon": "platforms/one.png", "sha256": "a" * 64},
                            {"name": "Two", "icon": "platforms/two.png", "sha256": "b" * 64},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = replace_platform_icons(
                {"One": source_one, "Two": source_two}, catalog_path, platforms_dir
            )
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

            self.assertEqual(result["catalog_version"], "1.0.6")
            self.assertEqual(result["replaced"], ["One", "Two"])
            self.assertEqual((platforms_dir / "one.png").read_bytes(), b"new-one")
            self.assertEqual((platforms_dir / "two.png").read_bytes(), b"new-two")
            self.assertNotEqual(catalog["platforms"][0]["sha256"], "a" * 64)
            self.assertNotEqual(catalog["platforms"][1]["sha256"], "b" * 64)

    def test_replace_rejects_unknown_platform_without_modifying_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            platforms_dir = root / "platforms"
            platforms_dir.mkdir()
            target = platforms_dir / "one.png"
            target.write_bytes(b"old-one")
            source = root / "source.png"
            source.write_bytes(b"new-one")
            catalog_path = root / "catalog.json"
            original_catalog = json.dumps(
                {
                    "schema_version": 1,
                    "catalog_version": "1.0.5",
                    "platforms": [
                        {"name": "One", "icon": "platforms/one.png", "sha256": "a" * 64}
                    ],
                }
            )
            catalog_path.write_text(original_catalog, encoding="utf-8")

            with self.assertRaises(ValueError):
                replace_platform_icons({"Missing": source}, catalog_path, platforms_dir)

            self.assertEqual(target.read_bytes(), b"old-one")
            self.assertEqual(catalog_path.read_text(encoding="utf-8"), original_catalog)


if __name__ == "__main__":
    unittest.main()
