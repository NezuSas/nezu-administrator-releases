#!/usr/bin/env python3
"""Safely add one platform icon to the signed NEZU catalog."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
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


def _load_catalog(catalog_path: Path) -> tuple[dict, list[dict]]:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    platforms = catalog.get("platforms")
    if catalog.get("schema_version") != 1 or not isinstance(platforms, list):
        raise ValueError("Unsupported catalog format.")
    return catalog, platforms


def _validate_icon_source(icon_source: Path) -> str:
    if not icon_source.is_file():
        raise ValueError(f"Icon file was not found: {icon_source}")
    suffix = icon_source.suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("Icon must be PNG, JPG, JPEG, WEBP, or SVG.")
    return suffix


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def add_platform(name: str, icon_source: Path, catalog_path: Path, platforms_dir: Path) -> dict[str, str]:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Platform name is required.")
    suffix = _validate_icon_source(icon_source)

    catalog, platforms = _load_catalog(catalog_path)
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


def replace_platform_icons(
    replacements: dict[str, Path], catalog_path: Path, platforms_dir: Path
) -> dict[str, object]:
    """Replace existing icons as one catalog revision and refresh their digests."""
    if not replacements:
        raise ValueError("At least one replacement is required.")

    catalog, platforms = _load_catalog(catalog_path)
    by_name = {item.get("name", "").casefold(): item for item in platforms}
    prepared: list[tuple[str, Path, dict, Path, bytes]] = []
    seen: set[str] = set()

    for requested_name, icon_source in replacements.items():
        clean_name = requested_name.strip()
        folded_name = clean_name.casefold()
        if not clean_name or folded_name in seen:
            raise ValueError(f"Invalid or duplicate platform replacement: {requested_name}")
        seen.add(folded_name)
        _validate_icon_source(icon_source)
        item = by_name.get(folded_name)
        if item is None:
            raise ValueError(f"Platform does not exist: {clean_name}")
        target = platforms_dir / Path(item["icon"]).name
        if not target.is_file():
            raise ValueError(f"Catalog icon file was not found: {target}")
        if target.suffix.lower() != icon_source.suffix.lower():
            raise ValueError(
                f"Replacement extension must remain {target.suffix.lower()} for {item['name']}."
            )
        prepared.append((item["name"], icon_source, item, target, target.read_bytes()))

    replaced_targets: list[tuple[Path, bytes]] = []
    try:
        for name, icon_source, item, target, original_content in prepared:
            content = icon_source.read_bytes()
            _atomic_write(target, content)
            replaced_targets.append((target, original_content))
            item["sha256"] = hashlib.sha256(content).hexdigest()
        catalog["catalog_version"] = increment_patch(catalog["catalog_version"])
        catalog_content = (json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        _atomic_write(catalog_path, catalog_content)
    except Exception:
        for target, original_content in reversed(replaced_targets):
            _atomic_write(target, original_content)
        raise

    return {
        "replaced": [name for name, *_ in prepared],
        "catalog_version": catalog["catalog_version"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Add or replace NEZU platform assets.")
    parser.add_argument("--name", help="Platform display name to add")
    parser.add_argument("--icon", type=Path, help="Path to the icon to add")
    parser.add_argument(
        "--replace",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="Replace an existing platform icon; may be supplied more than once",
    )
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent
    catalog_path = repository / "assets" / "catalog.json"
    platforms_dir = repository / "assets" / "platforms"
    if args.replace:
        if args.name or args.icon:
            parser.error("--replace cannot be combined with --name or --icon")
        replacements: dict[str, Path] = {}
        for value in args.replace:
            if "=" not in value:
                parser.error("--replace must use NAME=PATH")
            name, raw_path = value.split("=", 1)
            replacements[name] = Path(raw_path)
        result = replace_platform_icons(replacements, catalog_path, platforms_dir)
    else:
        if not args.name or not args.icon:
            parser.error("--name and --icon are required when adding a platform")
        result = add_platform(args.name, args.icon, catalog_path, platforms_dir)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
