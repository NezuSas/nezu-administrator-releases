# NEZU Administrator Releases

This repository publishes the public artifacts used by NEZU Administrator.

## Platform assets

`assets/catalog.json` lists the available platforms and the SHA-256 digest of
each icon. Icons live in `assets/platforms/`; they are independent from the
executable release.

The Administrator accepts a catalog only when `assets/catalog.json.sig` is a
valid Ed25519 signature produced with the existing NEZU release key. It then
validates each icon digest before caching it locally.

### Publishing a new platform

1. Add its icon in `assets/platforms/`.
2. Add its name and relative icon path to `assets/catalog.json` and increment
   `catalog_version`.
3. Commit and push. The workflow signs the catalog automatically.

Before the first publication, add the existing `NEZU_RELEASE_PRIVATE_KEY_HEX`
secret to this repository: **Settings → Secrets and variables → Actions**.
The key never belongs in a file or commit.
