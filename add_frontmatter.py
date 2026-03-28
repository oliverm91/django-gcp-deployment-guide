import os

files = {
    "docs/index.md": "A comprehensive guide to deploying a Django web application on Google Cloud Platform using Cloud Run, Cloud SQL, and GitHub Actions.",
    "docs/01_gcp_setup.md": "Learn how to set up a new Google Cloud Platform project, enable APIs, and configure service accounts for secure access.",
    "docs/02_artifact_registry.md": "Create a private Docker Artifact Registry in GCP to tightly control and store your containerized Django app images.",
    "docs/03_cloud_sql.md": "Provision and securely connect a managed PostgreSQL database using Cloud SQL for your production Django application.",
    "docs/04_secret_manager.md": "Securely store environment variables, passwords, and Django SECRET_KEYs using GCP Secret Manager.",
    "docs/05_cloud_storage.md": "Configure Google Cloud Storage buckets to handle static files and user-uploaded media seamlessly via Django-storages.",
    "docs/06_dockerfile.md": "Write a production-ready Dockerfile optimized for running Django apps on Cloud Run using uv.",
    "docs/07_first_deploy.md": "Manually deploy your Dockerized Django app to Cloud Run for the first time to verify end-to-end functionality.",
    "docs/08_domain_ssl.md": "Map your custom domain name and automatically provision a managed SSL certificate for your Cloud Run service.",
    "docs/09_workload_identity.md": "Configure Keyless Workload Identity Federation so GitHub Actions can securely authenticate to GCP without JSON keys.",
    "docs/10_github_actions.md": "Build a completely automated CI/CD pipeline using GitHub Actions to test, build, run migrations, and deploy to Cloud Run.",
    "docs/11_quick_reference.md": "A quick reference guide and cheat sheet for every gcloud and deployment command used throughout the Cloud Run Django guide."
}

for path, desc in files.items():
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Skip if it already has frontmatter
    if content.startswith("---\n"):
        continue
        
    frontmatter = f"---\ndescription: \"{desc}\"\n---\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)
