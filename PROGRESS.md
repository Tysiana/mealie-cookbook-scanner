# mealie-cookbook-scanner — Progress Tracker

## Status: Active development — core flow working, refinements ongoing

---

## Completed

### Infrastructure
- [x] Project scaffold — all folders and files created
- [x] `Dockerfile` — python:3.12-slim + Tesseract + all apt deps
- [x] `docker-compose.yml` — convenience compose file with config volume
- [x] `requirements.txt` — all Python deps pinned to latest at install time
- [x] `.gitignore` — config/, __pycache__, .env etc.
- [x] `ruff.toml` — Python linter/formatter config
- [x] `.prettierrc` — JS/HTML formatter config
- [x] Git repo initialised, identity configured (Tysiana / calajustyna@gmail.com)

### Backend (`app/`)
- [x] `config.py` — load/save config JSON from `/app/config/config.json` (mounted volume)
- [x] `mealie.py` — all Mealie API interactions + `build_recipe_payload()`
- [x] `ocr.py` — Tesseract wrapper (RGB convert, pytesseract)
- [x] `claude.py` — `SYSTEM_PROMPT` constant, Anthropic API call, JSON fence stripping
- [x] `main.py` — FastAPI app: `/api/health`, `/api/config`, `/api/ocr`, `/api/structure`, `/api/structure-image`, `/api/import`, static mount
- [x] Prompt externalised to `app/prompts/recipe_extraction.md` — loaded at startup
- [x] Claude vision endpoint (`/api/structure-image`) — sends image directly, bypasses OCR
- [x] Hero image upload fixed — `PUT /api/recipes/{slug}/image` with multipart fields
- [x] Image token flow — upload FIRST, include returned token in recipe PUT payload
- [x] Model switched to `claude-haiku-4-5-20251001` (cheaper, no Pro plan API credits)

### Frontend (`app/static/index.html`)
- [x] Config view (Mealie URL, token, Anthropic key) with prefill on reconfigure
- [x] Default Mealie URL set to `http://localhost:9925`
- [x] Upload view — 3-panel layout: scan, review OCR, hero image
- [x] Camera detection (mobile gets `capture="environment"` button, desktop gets drag-drop)
- [x] Canvas crop tool (mouse + touch) for extracting hero image from scan
- [x] Hero image tabs: crop from scan / separate upload / skip
- [x] Processing view with spinner + step-by-step status messages
- [x] Success view with direct Mealie link + "Import another" button
- [x] Warm cream / parchment theme (#fdf8f0 bg, #6b9080 sage green accent)
- [x] Nunito 20px font, logo wired from `app/imgs/mealiescancon.png` (256×256, 80 KB)
- [x] Logo 44px in header, 72px on config hero
- [x] **Rotate in scan panel** — ↺/↻ buttons, preview canvas, manual "Run OCR →"
- [x] **Column splitter in scan panel** — "📏 Columns" toggle beside rotate, draggable divider, auto-used by "Run OCR →" when active
- [x] **Claude Vision bypass** — "⚡ Claude Vision" in review panel button row, skips OCR entirely
- [x] **Hero upload rotate** — ↺/↻ buttons bake rotation into image before crop
- [x] **Hero upload crop fix** — button always enabled; "Use full image →" when no selection, "Crop selection →" when area drawn
- [x] **Crop overlay bug fixed** — canvas-space coords now divided by scale before use as drawImage source
- [x] OCR ingredient warning banner in review panel
- [x] Config returns token + API key for prefill on reconfigure

### Container
- [x] Image builds successfully: `mealie-cookbook-scanner:latest`
- [x] Workaround documented for Bazzite (Podman binary broken — use Docker static CLI via socket)
- [x] `/api/health` responds `{"status":"ok"}`
- [x] Frontend served correctly at `/`
- [x] OCR endpoint working — Tesseract extracting text inside container
- [x] End-to-end import verified (marbled banana bread recipe landed in Mealie)

---

### Security & Code Quality (code-review pass)
- [x] XSS — `showMsg`, `addProcessStep`, `showSuccess` use DOM API instead of `innerHTML`
- [x] `GET /api/config` returns `mealie_token_set`/`anthropic_key_set` booleans, never raw credentials
- [x] `AppConfig` dataclass replaces raw `dict` throughout backend
- [x] `main.py` split into `app/routes/{config,ocr,structure,import_recipe}.py`
- [x] `app/image_utils.py` — image helpers extracted from main.py
- [x] `mealie.py`: shared `httpx.AsyncClient` across import flow; `_validate_slug`; `_headers` private
- [x] `claude.py`: `SYSTEM_PROMPT` → `_SYSTEM_PROMPT`
- [x] File upload: content-type allowlist + 10 MB size guard before `read()`
- [x] `json.JSONDecodeError` caught specifically; entity context in all error messages
- [x] `.gitignore`: added `.ruff_cache/`, `.pytest_cache/`, editor/OS noise

### Distribution
- [x] `README.md` — what it does, prerequisites, one-command install, how it works, layout
- [ ] GitHub repo created + code pushed
- [ ] GitHub Actions — build + push to `ghcr.io` on push to `main`
- [ ] Final run command with `ghcr.io/YOURUSERNAME/mealie-cookbook-scanner:latest`

### Testing
- [x] `tests/` scaffold — `conftest.py`, fixtures, `pytest.ini`
- [x] `tests/test_config.py` — load/save/validation unit tests
- [x] `tests/test_image_utils.py` — resize + format unit tests
- [x] `tests/test_mealie.py` — slug validation + payload builder tests
- [x] `tests/test_routes_config.py` — HTTP-level integration tests for config endpoints
- [x] `pytest` + `pytest-asyncio` added to `requirements.txt`

---

## Remaining

### Distribution
- [ ] GitHub repo created + code pushed
- [ ] GitHub Actions — build + push to `ghcr.io` on push to `main`

### Nice to Have / Future
- [ ] Deploy to home Debian server (alongside Mealie on port 8090)
- [ ] Mobile UX pass — camera capture on phone
- [ ] Integration tests for OCR, structure, import routes (require mocked Tesseract / Anthropic / Mealie)

---

## Known Notes

- Bazzite: `/run/host/usr/bin/podman` fails (missing `libsubid.so.5`). Use Docker static CLI at `~/.local/bin/docker` via Podman socket.
- Podman 5.7.1 on Bazzite — no `--tail` flag, use `2>&1 | tail -N`.
- Claude Pro plan does NOT include API credits — purchase separately at console.anthropic.com.
- Mealie image upload: `PUT /api/recipes/{slug}/image` returns `{"image": "<token>"}` — must include token in recipe PUT as `"image": token`.
- Prompt file: `app/prompts/recipe_extraction.md` — edit here to tune extraction quality.

---

## Build Commands (Bazzite)

```bash
# Build image
DOCKER_HOST=unix:///run/user/1000/podman/podman.sock ~/.local/bin/docker build -t mealie-cookbook-scanner:latest .

# Run for testing
DOCKER_HOST=unix:///run/user/1000/podman/podman.sock ~/.local/bin/docker run -d \
  --name mealie-scanner \
  -p 8090:8090 \
  -v mealie-scanner-config:/app/config \
  mealie-cookbook-scanner:latest

# Logs
DOCKER_HOST=unix:///run/user/1000/podman/podman.sock ~/.local/bin/docker logs mealie-scanner 2>&1 | tail -50

# Stop + remove
DOCKER_HOST=unix:///run/user/1000/podman/podman.sock ~/.local/bin/docker rm -f mealie-scanner
```
