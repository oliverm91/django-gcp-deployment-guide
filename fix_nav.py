import os

docs2 = "C:/dev/gcp-deploy-guide/docs2"
os.chdir(docs2)

# (filename, display_title, es_filename)
nav = [
    ("01_introduction.md", "01 — Introduction: What We're Building", "01_introduction.es.md"),
    ("02_terraform_overview.md", "02 — Terraform Overview", "02_terraform_overview.es.md"),
    ("03_cloud_services.md", "03 — Cloud Services Explained", "03_cloud_services.es.md"),
    ("04_planetscale.md", "04 — PlanetScale Database Explained", "04_planetscale.es.md"),
    ("05_project_setup.md", "05 — Project Setup & Terraform State", "05_project_setup.es.md"),
    ("06_gcp_project.md", "06 — GCP Project & APIs", "06_gcp_project.es.md"),
    ("07_artifact_registry.md", "07 — Artifact Registry", "07_artifact_registry.es.md"),
    ("09_secrets.md", "08 — Secrets Management", "09_secrets.es.md"),
    ("10_storage.md", "09 — Cloud Storage", "10_storage.es.md"),
    ("11_iam.md", "10 — Service Accounts & IAM", "11_iam.es.md"),
    ("12_cloud_run.md", "11 — Cloud Run", "12_cloud_run.es.md"),
    ("13_tasks.md", "12 — Cloud Tasks & Scheduler", "13_tasks.es.md"),
    ("14_dockerfile.md", "13 — Dockerfile", "14_dockerfile.es.md"),
    ("15_first_deploy.md", "14 — First Deploy", "15_first_deploy.es.md"),
    ("16_domain_ssl.md", "15 — Custom Domain & SSL", "16_domain_ssl.es.md"),
    ("17_wif.md", "16 — Workload Identity Federation", "17_wif.es.md"),
    ("18_github_actions.md", "17 — GitHub Actions CI/CD", "18_github_actions.es.md"),
    ("19_quick_reference.md", "18 — Quick Reference", "19_quick_reference.es.md"),
]

nav_footer_en = """

## Navigation



"""

nav_footer_es = """

## Navegación



"""

files_en = [f for f, _, _ in nav]
files_es = [es for _, _, es in nav]

# Fix English navs
for i, (fname, title, _) in enumerate(nav):
    with open(fname, encoding='utf-8') as f:
        content = f.read()

    # Remove old nav section
    idx = content.find('## Navigation')
    if idx >= 0:
        content = content[:idx]

    lines = []
    for j, (f, t, _) in enumerate(nav):
        if fname == f:
            lines.append(f"- {t} (Current chapter)")
        else:
            lines.append(f"- [{t}]({f})")

    content = content.rstrip() + nav_footer_en + '\n'.join(lines)
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed EN nav: {fname}")

# Fix Spanish navs
for i, (_, title, es_fname) in enumerate(nav):
    with open(es_fname, encoding='utf-8') as f:
        content = f.read()

    idx = content.find('## Navegación')
    if idx >= 0:
        content = content[:idx]

    lines = []
    for j, (_, t, ef) in enumerate(nav):
        if es_fname == ef:
            lines.append(f"- {t} (Capítulo actual)")
        else:
            lines.append(f"- [{t}]({ef})")

    content = content.rstrip() + nav_footer_es + '\n'.join(lines)
    with open(es_fname, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed ES nav: {es_fname}")
