# NEZU Administrator Releases — guía para agentes

## Propósito

Este repositorio distribuye releases verificables y el catálogo remoto de
plataformas. Un cambio aquí puede llegar a todos los clientes: prioriza
integridad, trazabilidad y compatibilidad.

## Estándar global

Este repositorio sigue [NEZU Engineering Standards](https://github.com/NezuSas/nezu-engineering-standards).
Las reglas de esta guía prevalecen cuando sean más específicas para releases y firma.

## Roles de trabajo

### Catálogo de plataformas

- Añade logos con `tools/add-platform.ps1` o `tools/add_platform.py`.
- Acepta solamente PNG, JPG/JPEG, WEBP o SVG legibles, de origen autorizado y con un nombre de plataforma claro.
- No edites hashes manualmente: el script calcula SHA-256 y aumenta la versión del catálogo.
- Añade varias plataformas en un solo commit cuando sea posible para generar una sola firma automática.

### Seguridad y firma

- `assets/catalog.json` y `assets/catalog.json.sig` deben validarse con Ed25519.
- La clave privada vive solo en el secreto `NEZU_RELEASE_PRIVATE_KEY_HEX` de GitHub Actions. Nunca se guarda en Git, archivos locales, logs ni conversaciones.
- La clave pública fijada en la aplicación no se cambia sin una migración de confianza explícita.
- No publiques binarios ni metadata de actualización sin sus verificaciones criptográficas.

### Release manager

- Revisa que el repositorio esté limpio antes de modificarlo.
- Ejecuta pruebas de los scripts antes de `commit` y `push`:

  ```powershell
  python -m unittest discover -s tests -v
  ```

- El `push` de cambios en `assets/catalog.json` o `assets/platforms/` activa `Sign NEZU platform catalog`.
- No declares un catálogo disponible hasta que ese workflow esté en verde.

### QA de distribución

- Antes de publicar, confirma que los scripts pasan pruebas, que cada recurso tiene hash y que el catálogo no contiene duplicados ni rutas inseguras.
- Tras cada push de catálogo, verifica que `Sign NEZU platform catalog` termina en verde antes de comunicar disponibilidad.
- Para releases de la aplicación, comprueba que la metadata, firma y binario corresponden a la misma versión.

## Reglas de Git

- No sobrescribas cambios ajenos, no fuerces pushes y no elimines releases o recursos publicados.
- `commit` y `push` requieren autorización explícita del usuario.
- Si GitHub Actions crea el commit de firma antes de tu siguiente cambio, sincroniza con `git pull --rebase origin main` antes de continuar.

## Procedimiento de alta de una plataforma

1. Obtén un logo con permiso de uso y guárdalo localmente.
2. Ejecuta, por ejemplo:

   ```powershell
   .\tools\add-platform.ps1 -Name "Banco Guayaquil" -IconPath "C:\Users\ocuen\Downloads\bancoguayaquil.png"
   ```

3. Espera el workflow de firma en verde.
4. Clientes con una versión compatible descargarán el catálogo firmado al tener Internet y conservarán el icono en caché para uso offline.
