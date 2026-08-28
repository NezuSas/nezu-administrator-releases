#!/usr/bin/env python3
"""Safely add one platform icon to the signed NEZU catalog."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import unicodedata
from pathlib import Path

ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    if not slug:
        raise ValueError("The platform name must contain letters or numbers.")
    return slug


def increment_patch(version: str) -> str:
    try:
        major, minor, patch = (int(part) for part in version.split("."))
    except ValueError as exc:
        raise ValueError("catalog_version must use major.minor.patch format.") from exc
    if min(major, minor, patch) < 0:
        raise ValueError("catalog_version cannot contain negative numbers.")
    return f"{major}.{minor}.{patch + 1}"


def add_platform(name: str, icon_source: Path, catalog_path: Path, platforms_dir: Path) -> dict[str, str]:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Platform name is required.")
    if not icon_source.is_file():
        raise ValueError(f"Icon file was not found: {icon_source}")
    suffix = icon_source.suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("Icon must be PNG, JPG, JPEG, WEBP, or SVG.")

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    platforms = catalog.get("platforms")
    if catalog.get("schema_version") != 1 or not isinstance(platforms, list):
        raise ValueError("Unsupported catalog format.")
    if any(item.get("name", "").casefold() == clean_name.casefold() for item in platforms):
        raise ValueError(f"Platform already exists: {clean_name}")

    filename = slugify(clean_name) + suffix
    target = platforms_dir / filename
    if target.exists():
        raise ValueError(f"An icon already exists at: {target}")

    platforms_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(icon_source, target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    platforms.append({"name": clean_name, "icon": f"platforms/{filename}", "sha256": digest})
    catalog["catalog_version"] = increment_patch(catalog["catalog_version"])
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"name": clean_name, "icon": f"platforms/{filename}", "catalog_version": catalog["catalog_version"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a NEZU platform asset to the catalog.")
    parser.add_argument("--name", required=True, help="Platform display name")
    parser.add_argument("--icon", required=True, type=Path, help="Path to a PNG/JPG/WEBP/SVG icon")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent
    result = add_platform(args.name, args.icon, repository / "assets" / "catalog.json", repository / "assets" / "platforms")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
