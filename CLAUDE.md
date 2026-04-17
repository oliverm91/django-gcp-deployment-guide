# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A documentation site (MkDocs Material) for a step-by-step guide to deploying Django on GCP (Cloud Run, Cloud SQL, Cloud Storage, Secret Manager, Artifact Registry, GitHub Actions, Workload Identity Federation). The Python code here is tooling to manage the docs, not a Django app itself.

## Commands

This project uses `uv` for dependency management (Python 3.14).

```bash
# Install dependencies
uv venv
uv pip install mkdocs-material mkdocs-static-i18n

# Serve docs locally with live reload
uv run mkdocs serve

# Build static site
uv run mkdocs build

# Deploy to GitHub Pages (CI does this automatically on push to main)
uv run mkdocs gh-deploy --force
```

## Architecture

- `docs/` — Markdown source files for each chapter (`01_gcp_setup.md` … `12_custom_email.md`) plus `index.md`
- `docs/*.es.md` — Spanish translations; generated/synced via `make_es_files.py` (do not edit manually)
- `mkdocs.yml` — Site config: navigation order, i18n plugin (suffix strategy), Material theme, markdown extensions
- `overrides/main.html` — Custom Material theme template override
- `.github/workflows/docs.yml` — CI: installs deps with uv, runs `mkdocs gh-deploy` on every push to `main`

### i18n Strategy

The `mkdocs-static-i18n` plugin uses the **suffix** convention: `page.md` = English default, `page.es.md` = Spanish. Internal links in `.es.md` files still point to `.md` filenames — the plugin resolves them to the correct locale automatically.

### Utility Scripts

| Script | Purpose |
|---|---|
| `make_es_files.py` | Creates/updates `.es.md` files from their English counterparts; handles structural nav-link translations |
| `add_frontmatter.py` | Adds `description:` YAML frontmatter to English docs that lack it |
| `update_image_frontmatter.py` | Injects `image: assets/social-banner.png` into frontmatter of docs missing it |

Run these scripts from the repo root with `python <script>.py` or `uv run python <script>.py`.

## Content Conventions

- Each chapter file starts with YAML frontmatter (`description:`, `image:`)
- Navigation footers use `← [Previous: …]` / `[Next: …] →` links at the bottom of each chapter
- Chapter 12 is the last chapter; `index.md` lists all 12 chapters
