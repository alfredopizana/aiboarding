# SPEC-003 — Ingesta y Conectores

**Estado:** Aprobado · **Versión:** 1.0

## 1. Contrato

Todo conector implementa:

```python
class Connector(ABC):
    name: str
    def is_configured(self) -> bool: ...
    def fetch(self) -> Iterable[SourceDocument]: ...
```

`SourceDocument`:

| Campo | Tipo | Descripción |
|---|---|---|
| `doc_id` | str | Estable y único (`sha1(source:uri)`) |
| `source` | `local\|confluence\|gdrive\|github` | Origen |
| `title` | str | Título legible |
| `uri` | str | Ruta o URL canónica a la fuente |
| `content` | str | Texto plano extraído |
| `metadata` | dict | space, repo, mime, updated_at… |

## 2. Conectores Fase 1

### 2.1 Local (`connectors/local.py`)
- Entrada: directorio raíz (`docs_dir`).
- Soporta: `.md`, `.txt`, `.pdf` (vía `pypdf`), recursivo.
- `uri` = ruta absoluta del archivo.

### 2.2 Confluence (`connectors/confluence.py`)
- REST API v2 (`/wiki/api/v2/pages?body-format=storage`), auth básica email+token.
- Limpia HTML del storage format → texto.
- Paginación por cursor (`_links.next`).

### 2.3 Google Drive (`connectors/gdrive.py`)
- `google-api-python-client` (extra `[gdrive]`); exporta Google Docs a text/plain,
  descarga PDFs y los extrae con pypdf.
- Configuración: `GDRIVE_CREDENTIALS_PATH`, `GDRIVE_FOLDER_IDS`.
- Si el extra no está instalado → `is_configured() == False` (skip limpio).

### 2.4 GitHub (`connectors/github.py`)
- REST API (`httpx`), token PAT; repos en `GITHUB_REPOS` (csv `org/repo`).
- Ingiere `README*`, `docs/**/*.md`, `*.md` raíz (git tree recursivo, filtro por extensión).

## 3. Chunking

- Split por párrafos, target 1200 chars, overlap 200 chars, sin cortar palabras.
- `chunk_id = f"{doc_id}:{n}"`; cada chunk hereda `title`, `uri`, `source`.

## 4. Idempotencia

Re-ingerir un `doc_id` reemplaza sus chunks anteriores (upsert por prefijo de `doc_id`).

## 5. CLI

```
aiboarding ingest --source local --path ./data/sample_docs
aiboarding ingest --source confluence
aiboarding ingest --source github
aiboarding ingest --source all
```
