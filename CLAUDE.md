# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A documentation site (MkDocs Material) for step-by-step guides to deploying Django on cloud platforms. This repo contains two guides:

- **`docs/`** — Original GCP guide (Cloud Run, Cloud SQL, Artifact Registry, GitHub Actions, Workload Identity Federation)
- **`docs2/`** — Terraform-based guide (GCP with Terraform, PlanetScale Postgres instead of Cloud SQL, Cloud Tasks for background jobs)

The Python code here is tooling to manage the docs, not a Django app itself.

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

- `docs/` — Markdown source files for original GCP guide (chapters `01_gcp_setup.md` … `13_django_tasks.md`) plus `index.md`
- `docs2/` — Markdown source files for Terraform-based guide (chapters `01_introduction.md` … `19_quick_reference.md`) plus `index.md`; uses GCP + PlanetScale + Terraform
- `docs/*.es.md` — Spanish translations for docs/; generated/synced via `make_es_files.py` (do not edit manually)
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

### All chapters
- Each chapter file starts with YAML frontmatter (`description:`, `image:`)
- Navigation footers use `← [Previous: …]` / `[Next: …] →` links at the bottom of each chapter

### docs/ (original GCP guide)
- 13 chapters + quick reference
- Uses Cloud SQL for Postgres

### docs2/ (Terraform guide)
- 19 chapters + quick reference
- Uses PlanetScale for Postgres (no foreign keys — use `db_constraint=False`)
- All infrastructure defined in Terraform
