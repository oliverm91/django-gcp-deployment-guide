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

# context-mode — MANDATORY routing rules

You have context-mode MCP tools available. These rules are NOT optional — they protect your context window from flooding. A single unrouted command can dump 56 KB into context and waste the entire session.

## BLOCKED commands — do NOT attempt these

### curl / wget — BLOCKED
Any Bash command containing `curl` or `wget` is intercepted and replaced with an error message. Do NOT retry.
Instead use:
- `ctx_fetch_and_index(url, source)` to fetch and index web pages
- `ctx_execute(language: "javascript", code: "const r = await fetch(...)")` to run HTTP calls in sandbox

### Inline HTTP — BLOCKED
Any Bash command containing `fetch('http`, `requests.get(`, `requests.post(`, `http.get(`, or `http.request(` is intercepted and replaced with an error message. Do NOT retry with Bash.
Instead use:
- `ctx_execute(language, code)` to run HTTP calls in sandbox — only stdout enters context

### WebFetch — BLOCKED
WebFetch calls are denied entirely. The URL is extracted and you are told to use `ctx_fetch_and_index` instead.
Instead use:
- `ctx_fetch_and_index(url, source)` then `ctx_search(queries)` to query the indexed content

## REDIRECTED tools — use sandbox equivalents

### Bash (>20 lines output)
Bash is ONLY for: `git`, `mkdir`, `rm`, `mv`, `cd`, `ls`, `npm install`, `pip install`, and other short-output commands.
For everything else, use:
- `ctx_batch_execute(commands, queries)` — run multiple commands + search in ONE call
- `ctx_execute(language: "shell", code: "...")` — run in sandbox, only stdout enters context

### Read (for analysis)
If you are reading a file to **Edit** it → Read is correct (Edit needs content in context).
If you are reading to **analyze, explore, or summarize** → use `ctx_execute_file(path, language, code)` instead. Only your printed summary enters context. The raw file content stays in the sandbox.

### Grep (large results)
Grep results can flood context. Use `ctx_execute(language: "shell", code: "grep ...")` to run searches in sandbox. Only your printed summary enters context.

## Tool selection hierarchy

1. **GATHER**: `ctx_batch_execute(commands, queries)` — Primary tool. Runs all commands, auto-indexes output, returns search results. ONE call replaces 30+ individual calls.
2. **FOLLOW-UP**: `ctx_search(queries: ["q1", "q2", ...])` — Query indexed content. Pass ALL questions as array in ONE call.
3. **PROCESSING**: `ctx_execute(language, code)` | `ctx_execute_file(path, language, code)` — Sandbox execution. Only stdout enters context.
4. **WEB**: `ctx_fetch_and_index(url, source)` then `ctx_search(queries)` — Fetch, chunk, index, query. Raw HTML never enters context.
5. **INDEX**: `ctx_index(content, source)` — Store content in FTS5 knowledge base for later search.

## Subagent routing

When spawning subagents (Agent/Task tool), the routing block is automatically injected into their prompt. Bash-type subagents are upgraded to general-purpose so they have access to MCP tools. You do NOT need to manually instruct subagents about context-mode.

## Output constraints

- Keep responses under 500 words.
- Write artifacts (code, configs, PRDs) to FILES — never return them as inline text. Return only: file path + 1-line description.
- When indexing content, use descriptive source labels so others can `ctx_search(source: "label")` later.

## ctx commands

| Command | Action |
|---------|--------|
| `ctx stats` | Call the `ctx_stats` MCP tool and display the full output verbatim |
| `ctx doctor` | Call the `ctx_doctor` MCP tool, run the returned shell command, display as checklist |
| `ctx upgrade` | Call the `ctx_upgrade` MCP tool, run the returned shell command, display as checklist |
