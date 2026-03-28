---
description: "Step 10: Build a completely automated CI/CD pipeline using GitHub Actions to test, build, run migrations, and deploy to Cloud Run."
image: assets/social-banner.png
---
# 10 — GitHub Actions CI/CD Pipeline

← [Anterior: 09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)

> ✅ **Free for most usage.** GitHub Actions gives 2,000 free minutes/month for private repositories and unlimited minutes for public repositories. Each deploy run (tests + build + push + deploy) takes roughly 5–10 minutes, giving you ~200–400 free deploys/month on a private repo. After the free tier, additional minutes cost $0.008/minute.

## What is GitHub Actions?

GitHub Actions is GitHub's built-in automation platform. You define workflows in YAML files inside `.github/workflows/`. GitHub runs them on its own servers (called runners) in response to events — a push, a pull request, a schedule.

The workflow here runs on every push to `main` and every pull request targeting `main`. It has two jobs:

- **test** — runs on all pushes and PRs; blocks the deploy if it fails
- **deploy** — runs only on pushes to `main` (not on PRs); only runs if `test` passes

---

## Create the workflow file

Create `.github/workflows/deploy.yml` at the **repo root**:

```yaml
name: Test & Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGION: southamerica-east1
  IMAGE: southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app

jobs:
  # ── Job 1: test ──────────────────────────────────────────────────────────────
  # Runs on every push and PR. Blocks deploy if tests fail.
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        # Checks out your repo code onto the runner

      - uses: astral-sh/setup-uv@v4
        with:
          working-directory: web
        # Installs uv (the package manager) on the runner

      - name: Install dependencies
        run: cd web && uv sync --frozen
        # Installs all Python dependencies from uv.lock
        # --frozen: fail if lockfile is out of date

      - name: Run tests
        run: cd web && uv run manage.py test web/tests --settings=core.settings.test
        # Runs the Django test suite using SQLite in-memory (no DB needed)
        env:
          SECRET_KEY: ci-secret-not-real
          # test.py requires SECRET_KEY to be set; this dummy value is fine for tests

  # ── Job 2: deploy ────────────────────────────────────────────────────────────
  # Runs only on pushes to main, only if the test job passed.
  deploy:
    runs-on: ubuntu-latest
    needs: test                              # wait for test job to succeed
    if: github.ref == 'refs/heads/main'      # skip on pull requests

    permissions:
      contents: read
      id-token: write                        # required for Workload Identity token exchange

    steps:
      - uses: actions/checkout@v4

      # Authenticate to GCP using Workload Identity (no JSON keys)
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      # Install gcloud CLI on the runner
      - uses: google-github-actions/setup-gcloud@v2

      # Configure Docker to push to Artifact Registry
      - name: Configure Docker
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet

      # Build the Docker image with two tags:
      # - :latest (always points to newest)
      # - :<git-sha> (unique per commit — enables precise rollbacks)
      - name: Build image
        run: |
          docker build \
            -t ${{ env.IMAGE }}:${{ github.sha }} \
            -t ${{ env.IMAGE }}:latest \
            .

      # Push both tags to Artifact Registry
      - name: Push image
        run: docker push --all-tags ${{ env.IMAGE }}

      # Update the migrate job to use the new image, then run it
      # This applies any new database migrations before traffic hits the new code
      - name: Run migrations
        run: |
          gcloud run jobs update migrate \
            --image=${{ env.IMAGE }}:${{ github.sha }} \
            --region=${{ env.REGION }}
          gcloud run jobs execute migrate \
            --region=${{ env.REGION }} \
            --wait

      # Deploy the new image to Cloud Run
      # Cloud Run creates a new revision and shifts 100% of traffic to it
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy mycoolproject \
            --image=${{ env.IMAGE }}:${{ github.sha }} \
            --region=${{ env.REGION }}
```

---

## What happens on each push to main

```
push to main
    │
    ├── test job
    │     ├── checkout code
    │     ├── install uv + dependencies
    │     └── run Django test suite (171 tests, ~90 seconds)
    │                   │
    │              fails? → deploy job is skipped, broken code never reaches prod
    │              passes? ↓
    │
    └── deploy job
          ├── authenticate to GCP (Workload Identity)
          ├── docker build (uses layer cache — fast if deps unchanged)
          ├── docker push → Artifact Registry
          ├── update migrate job image
          ├── run migrate job → applies DB migrations → waits for completion
          └── gcloud run deploy → new Cloud Run revision goes live
```

## What happens on a pull request

Only the `test` job runs. The deploy job is skipped because `github.ref` is not `refs/heads/main`. This means every PR gets its tests run, but the live site is only updated when code merges to `main`.

---

## Rollback

If a bad deploy slips through, roll back to the previous revision in seconds:

```bash
# Lists recent revisions with their names and traffic split — find the last good revision name here.
gcloud run revisions list --service=mycoolproject --region=southamerica-east1

# Shifts 100% of traffic to a specific revision, instantly rolling back the live site.
# Replace mycoolproject-<previous-revision> with the revision name from the list command above.
# Result: the site immediately serves the old revision — no rebuild needed.
gcloud run services update-traffic mycoolproject \
  --region=southamerica-east1 \
  --to-revisions=mycoolproject-<previous-revision>=100
```

Or re-run the previous commit's GitHub Actions workflow — it redeploys the image tagged with that commit's SHA.

---

## 📖 Navegación

- [01 — GCP Project Setup](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (PostgreSQL Database)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Media & Static Files)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — First Deploy](07_first_deploy.md)
- [08 — Custom Domain & SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)
- **10 — GitHub Actions CI/CD Pipeline** (capítulo actual)
- [11 — Quick Reference](11_quick_reference.md)
