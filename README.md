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

From PowerShell, run this single command inside the repository:

```powershell
.\tools\add-platform.ps1
```

It asks for the platform name and the icon path, then calculates the SHA-256,
increments `catalog_version`, copies the image, commits and pushes the change.
GitHub Actions signs the catalog automatically. The repository must be clean
before it runs, so unrelated files are never included in its commit.

You can also supply both values directly:

```powershell
.\tools\add-platform.ps1 -Name "Discord" -IconPath "C:\Images\discord.png"
```

### Replacing existing icons

Use the Python helper to replace one or more existing icons in a single catalog
revision. It validates every platform and source before writing, refreshes each
SHA-256, and increments `catalog_version` only once:

```powershell
python .\tools\add_platform.py `
  --replace "Banco Guayaquil=C:\Images\banco-guayaquil.png" `
  --replace "VIGI=C:\Images\vigi.png"
```

Keep the existing file extension and record the official source in
[`assets/SOURCES.md`](assets/SOURCES.md). Do not edit catalog digests manually.

For example, to publish Banco Guayaquil from a downloaded logo:

```powershell
.\tools\add-platform.ps1 -Name "Banco Guayaquil" -IconPath "C:\Users\ocuen\Downloads\bancoguayaquil.png"
```
Before the first publication, add the existing `NEZU_RELEASE_PRIVATE_KEY_HEX`
secret to this repository: **Settings → Secrets and variables → Actions**.
The key never belongs in a file or commit.
