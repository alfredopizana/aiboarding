# AIboarding — POC / MVP Setup (real services)

Guía para conectar AIboarding a servicios reales con **cuentas de prueba** y
correr la demo en local: web app (Streamlit) + bot de Slack + ingesta desde
Confluence / GitHub / Google Drive.

> 🔐 **Regla de oro de seguridad**
> Todos los secretos van en `.env` (ya está en `.gitignore`). **Nunca** los
> pongas en `.env.example` ni en ningún archivo trackeado. `credentials.json`
> (Google) también está gitignored. Como son cuentas de prueba desechables el
> riesgo es bajo, pero mantén el hábito.

---

## 0. Orden recomendado

Ve de lo más fácil/impactante a lo más laborioso. Puedes parar en cualquier punto: cada conector es independiente y los que no configures se marcan `skipped`.

| # | Servicio | Esfuerzo | ¿Imprescindible para la demo? |
|---|----------|----------|-------------------------------|
| 1 | **OpenAI** (LLM real) | 🟢 Bajo | Recomendado — sin esto la demo cita docs pero no redacta |
| 2 | **Slack** (canal de chat) | 🟡 Medio | Sí (lo pediste) |
| 3 | **GitHub** (docs de repo) | 🟢 Bajo | Opcional |
| 4 | **Confluence** (wiki) | 🟡 Medio | Opcional |
| 5 | **Google Drive** | 🔴 Alto | Opcional (el más pesado) |
| 6 | **SMTP email** (Fase 2) | 🟢 Bajo | Opcional |

Cada sección termina con las **líneas exactas del `.env`** que debes rellenar.

---

## 1. OpenAI — LLM + embeddings reales

Sin esto, `AIBOARDING_LLM_PROVIDER=fake` solo recupera y cita fragmentos. Para
que la demo **redacte respuestas** en lenguaje natural, usa OpenAI (barato:
`gpt-4o-mini` + `text-embedding-3-small` cuestan centavos para un POC).

1. Crea cuenta en <https://platform.openai.com>.
2. **Settings → Billing** → agrega ~$5 de crédito (las API keys no funcionan sin saldo).
3. **API keys** → *Create new secret key* → copia `sk-...` (solo se ve una vez).

```env
AIBOARDING_LLM_PROVIDER=openai
AIBOARDING_LLM_MODEL=gpt-4o-mini
AIBOARDING_EMBEDDINGS_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

> ⚠️ Si cambias de `hashing` a `openai` en embeddings **después** de haber
> ingerido docs, reingiere todo (los vectores viejos son incompatibles):
> borra `data/vectorstore/` y vuelve a correr `aiboarding ingest`.

---

## 2. Slack — bot de chat (Socket Mode)

El bot usa **Socket Mode** (no necesita URL pública ni ngrok — perfecto para local).

### 2.1 Crear workspace y app
1. Crea un workspace gratis en <https://slack.com/get-started>.
2. Ve a <https://api.slack.com/apps> → **Create New App** → **From scratch** →
   nombre `AIboarding` → elige tu workspace.

### 2.2 Activar Socket Mode + App-Level Token
3. Menú lateral **Socket Mode** → actívalo.
4. Te pedirá crear un **App-Level Token** con scope `connections:write`.
   Genéralo y copia el `xapp-...` → es tu `SLACK_APP_TOKEN`.

### 2.3 Permisos del bot (OAuth scopes)
5. **OAuth & Permissions → Bot Token Scopes**, agrega:
   - `app_mentions:read` — leer menciones `@AIboarding`
   - `chat:write` — responder
   - `im:history` + `im:read` — (opcional) responder en mensajes directos

### 2.4 Suscripción a eventos
6. **Event Subscriptions** → activa → **Subscribe to bot events**, agrega:
   - `app_mention`
   - `message.im` — (opcional, para DMs)

### 2.5 Instalar
7. **Install App** → *Install to Workspace* → autoriza.
8. Copia el **Bot User OAuth Token** `xoxb-...` → es tu `SLACK_BOT_TOKEN`.
9. En Slack, invita al bot a un canal: `/invite @AIboarding`.

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

Instalar dependencia y arrancar:
```bash
pip install -e '.[slack]'
aiboarding slack          # se queda escuchando; Ctrl+C para parar
```
Luego en Slack: `@AIboarding ¿cómo configuro mi entorno?`

---

## 3. GitHub — docs desde un repo

El conector lee archivos `.md/.mdx/.rst/.txt` que estén en la **raíz** del repo
o dentro de `docs/`.

1. Usa tu cuenta o crea una de prueba.
2. Crea un repo (puede ser **privado**), p.ej. `tu-usuario/aiboarding-demo-docs`,
   con algunos `.md` (ver sección 7 para contenido de prueba).
3. Genera un **Fine-grained Personal Access Token**:
   <https://github.com/settings/personal-access-tokens> → *Generate new token*
   - **Repository access**: Only select repositories → elige tu repo
   - **Permissions → Repository → Contents: Read-only**
   - (Alternativa rápida: token *classic* con scope `repo`)
4. Copia el token `github_pat_...`.

```env
GITHUB_TOKEN=github_pat_...
GITHUB_REPOS=tu-usuario/aiboarding-demo-docs
# varios repos separados por coma: owner/repo1,owner/repo2
```

---

## 4. Confluence — wiki (Atlassian Cloud)

Autenticación por **API Token** (basic auth: email + token). No es Forge ni OAuth.

1. Regístrate gratis en <https://www.atlassian.com/software/confluence> (tier
   gratuito hasta 10 usuarios). Obtendrás un sitio `https://<algo>.atlassian.net`.
2. Crea un **Space** y algunas páginas (ver sección 7).
3. Genera el token: <https://id.atlassian.com/manage-profile/security/api-tokens>
   → *Create API token* → nómbralo → copia (solo se ve una vez).

```env
CONFLUENCE_BASE_URL=https://<tu-sitio>.atlassian.net/wiki
CONFLUENCE_EMAIL=tu-email@ejemplo.com
CONFLUENCE_API_TOKEN=ATATT3x...
```

> El conector trae **todas las páginas que tu usuario puede ver** vía la REST
> API v2. Para un POC con un solo Space está perfecto.

---

## 5. Google Drive — el más laborioso (Service Account)

1. <https://console.cloud.google.com> → crea un **proyecto** nuevo.
2. **APIs & Services → Library** → busca **Google Drive API** → *Enable*.
3. **APIs & Services → Credentials → Create Credentials → Service account**.
   - Dale un nombre, créala.
   - En la service account → pestaña **Keys → Add Key → Create new key → JSON**.
   - Se descarga un JSON. Guárdalo en la raíz del repo como `credentials.json`
     (ya está gitignored).
   - Copia el **email** de la service account (algo como
     `xxx@proyecto.iam.gserviceaccount.com`).
4. En Google Drive, crea una **carpeta**, mete docs (Google Docs / PDF / .txt /
   .md) y **compártela** con ese email de la service account como **Lector**.
5. El **folder ID** es la parte final de la URL de la carpeta:
   `https://drive.google.com/drive/folders/<ESTE_ID>`.

```env
GDRIVE_CREDENTIALS_PATH=./credentials.json
GDRIVE_FOLDER_IDS=<folder_id>
# varias carpetas: id1,id2
```

Instalar dependencia:
```bash
pip install -e '.[gdrive]'
```

> Solo extrae **Google Docs** (export a texto), **PDF**, **.txt** y **.md**.
> Otros formatos (Sheets, Slides) se ignoran.

---

## 6. SMTP email (Fase 2, opcional)

Para enviar el plan de 90 días por correo. Para pruebas, lo más fácil es
**Mailtrap** (buzón de prueba, no envía a real) o un **App Password** de Gmail.

```env
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
EMAIL_FROM=onboarding-bot@ejemplo.com
```

---

## 6b. Persistencia (usuarios, planes, progreso)

Por defecto usa **SQLite** en un solo archivo (`data/aiboarding.db`, gitignored)
— sin servidor. Guarda usuarios, sus planes de 90 días y el progreso (qué ítems
completaron). La SPA identifica al usuario por email y trackea su avance.

```env
AIBOARDING_PROGRESS_BACKEND=sqlite      # sqlite | firebase (futuro)
AIBOARDING_DB_PATH=./data/aiboarding.db
```

La capa está abstraída tras `ProgressStore`, así que migrar a **Firebase** más
adelante es implementar una clase con la misma interfaz y cambiar el backend.

## 6c. Trazabilidad — LangSmith

El agente corre sobre LangGraph, así que se traza casi solo. Consigue una API
key gratis en <https://smith.langchain.com> → *Settings → API Keys*.

```env
AIBOARDING_LANGSMITH_TRACING=true
AIBOARDING_LANGSMITH_API_KEY=lsv2_...
AIBOARDING_LANGSMITH_PROJECT=aiboarding
```

Cada `aiboarding ask` / mensaje de Slack / consulta de la SPA aparece como un
trace con nodos, latencias, prompts y retrieval. Es complementario al audit
trail local (que sigue funcionando).

---

## 7. Correr todo

```bash
source .venv/bin/activate
pip install -e '.[ui,slack,gdrive]'      # todas las extras

# Ingerir de todas las fuentes configuradas (las no configuradas se saltan)
aiboarding ingest --source all
aiboarding info                          # verifica docs/chunks/provider

# Web app (local)
aiboarding ui                            # http://localhost:8501

# Bot de Slack (en otra terminal)
aiboarding slack
```

En la web app, la pestaña **⚙️ Admin** también permite disparar la ingesta y
revisar el **audit trail** por `thread_id`.

---

## 8. Checklist del `.env`

| Servicio | Claves a rellenar |
|----------|-------------------|
| OpenAI | `AIBOARDING_LLM_PROVIDER=openai`, `AIBOARDING_EMBEDDINGS_PROVIDER=openai`, `OPENAI_API_KEY` |
| Slack | `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` |
| GitHub | `GITHUB_TOKEN`, `GITHUB_REPOS` |
| Confluence | `CONFLUENCE_BASE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN` |
| Google Drive | `GDRIVE_CREDENTIALS_PATH`, `GDRIVE_FOLDER_IDS` (+ `credentials.json`) |
| Email | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM` |
