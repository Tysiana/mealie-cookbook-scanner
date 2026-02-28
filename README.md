# mealie-cookbook-scanner

Scan a physical recipe page → OCR it → let Claude structure it → import it straight into [Mealie](https://mealie.io).

Works entirely from the browser. No cloud sync, no account needed beyond your own Mealie instance and an Anthropic API key.

---

## What it does

1. **Scan** — upload or photograph a cookbook page. Rotate and crop, or use the column splitter for two-column layouts.
2. **OCR** — Tesseract extracts the text inside the container (no data leaves your machine for OCR).
3. **Structure** — Claude reads the raw text (or the image directly via vision) and returns structured JSON: title, ingredients, instructions, times, servings.
4. **Import** — one click sends everything to Mealie, including a hero image if you cropped one.

Multi-page recipes are supported: scan the second page and append it before sending to Claude.

---

## Prerequisites

- Docker (or Podman with the Docker CLI shim)
- A running Mealie instance and an API token for it
- An [Anthropic API key](https://console.anthropic.com) (billed per use; Claude Pro does **not** include API credits)

---

## Quick start

```bash
docker run -d \
  --name mealie-scanner \
  -p 8090:8090 \
  -v mealie-scanner-config:/app/config \
  ghcr.io/YOURUSERNAME/mealie-cookbook-scanner:latest
```

Open **http://localhost:8090** and follow the one-time setup wizard.

> **Bazzite / Podman users** — the system Podman binary may be broken. Use the Docker static CLI via the Podman socket:
> ```bash
> DOCKER_HOST=unix:///run/user/1000/podman/podman.sock ~/.local/bin/docker run ...
> ```

---

## Build locally

```bash
docker build -t mealie-cookbook-scanner:latest .
docker run -d \
  --name mealie-scanner \
  -p 8090:8090 \
  -v mealie-scanner-config:/app/config \
  mealie-cookbook-scanner:latest
```

---

## Configuration

On first launch the app asks for:

| Field | Where to find it |
|---|---|
| Mealie URL | Your Mealie base URL, e.g. `http://192.168.1.10:9925` |
| Mealie token | Mealie → Profile → API Tokens → Create |
| Anthropic key | console.anthropic.com → API Keys |

Credentials are stored in the named Docker volume (`mealie-scanner-config`) and never leave the container. The UI never displays them again after saving.

---

## How it works

```
Browser → FastAPI (port 8090)
             ├─ /api/ocr          — Tesseract (runs inside container)
             ├─ /api/structure    — Anthropic Claude (text → JSON)
             ├─ /api/structure-image — Claude vision (image → JSON, skips OCR)
             └─ /api/import       — Mealie REST API
```

The prompt used for extraction lives in `app/prompts/recipe_extraction.md` — edit it to tune Claude's output without touching code.

---

## Project layout

```
app/
  config.py          load/save config JSON from mounted volume
  claude.py          Anthropic API call + prompt loading
  mealie.py          Mealie REST helpers
  ocr.py             Tesseract wrapper
  image_utils.py     image resize/reformat for vision + hero upload
  routes/
    config.py        GET+POST /api/config, GET /api/health
    ocr.py           POST /api/ocr
    structure.py     POST /api/structure, /api/structure-image
    import_recipe.py POST /api/import
  prompts/
    recipe_extraction.md  Claude system prompt
  static/
    index.html       single-page frontend (vanilla JS, no build step)
  imgs/
    mealiescancon.png  app logo
```

---

## Tuning extraction quality

Edit `app/prompts/recipe_extraction.md` and rebuild the image. The file is the complete system prompt sent to Claude. Common tweaks:

- Add language-specific instructions for cookbooks not in English
- Tell Claude to preserve section headers as `sectionTitle` fields
- Adjust how it handles missing prep/cook times

---

## License

MIT
