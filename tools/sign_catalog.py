#!/usr/bin/env python3
"""Create a detached Ed25519 signature for the NEZU platform catalog."""
import argparse
import base64
import json
import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def canonical_catalog(catalog):
    payload = {
        "schema_version": catalog["schema_version"],
        "catalog_version": catalog["catalog_version"],
        "platforms": catalog["platforms"],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--signature", type=Path, required=True)
    args = parser.parse_args()
    secret = os.environ.get("NEZU_RELEASE_PRIVATE_KEY_HEX", "").strip()
    try:
        private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(secret))
        catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
        signature = base64.b64encode(private_key.sign(canonical_catalog(catalog))).decode("ascii")
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot sign platform catalog: {exc}")
    args.signature.write_text(signature + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
