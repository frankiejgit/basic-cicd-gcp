# Enterprise CI/CD on Google Cloud

This repository contains a reference architecture and quick-start demo for a fully serverless, enterprise-grade CI/CD pipeline on Google Cloud. 

It demonstrates deploying a Python (Flask) application from GitHub to Cloud Run, separating Continuous Integration (CI) from Continuous Delivery (CD), using least-privilege security, and implementing a manual approval step for production releases.

## Architecture

```text
[ Developer ]
     │ (git push)
     ▼
[ GitHub Repo ] ──(Developer Connect)──┐
                                       │
                                       ▼
                              [ Cloud Build (CI) ] (Executes cloudbuild.yaml via Custom SA)
                                       │
                                   (Build & Push)
                                       │
                                       ▼
[ Artifact Registry ] ◄────── [ Cloud Deploy (CD) ] (Manages the release pipeline)
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
           [ Cloud Run (Dev) ]                 [ Cloud Run (Prod) ]
             (us-central1)                         (us-east1)
         * Deploys automatically              * Pauses for Manual Approval
```

### Enterprise Best Practices Implemented
* **Separation of CI and CD:** Cloud Build strictly handles CI (building and pushing the immutable image). Cloud Deploy handles CD (promoting that exact same image across environments).
* **Developer Connect:** Uses Google's latest recommended V2 API to securely connect GitHub to Google Cloud.
* **Least Privilege Security:** Both Cloud Build and Cloud Deploy execute using a custom Service Account, rather than Google's over-permissive default compute accounts.
* **Modern Python Layout:** Uses the `src/` directory layout to prevent module shadowing.

---

## Repository Structure

* `src/main.py` - The Python Flask web application.
* `Dockerfile` - Simple, multi-threaded container configuration using Gunicorn.
* `cloudbuild.yaml` - Declarative pipeline configuration for Google Cloud Build.
* `service.yaml` - The Cloud Run Knative manifest.
* `skaffold.yaml` - Tells Cloud Deploy how to render and deploy `service.yaml`.
* `clouddeploy.yaml` - Infrastructure-as-code file defining the Dev and Prod pipeline stages.

---

## Setup Instructions

To deploy this architecture in your own Google Cloud project, follow these steps using Google Cloud Shell or your local terminal authenticated with `gcloud`.

### 1. Set Environment Variables
```bash
export PROJECT_ID=$(gcloud config get-value project)
export DEV_REGION="us-central1"
export PROD_REGION="us-east1"
export SA_NAME="cicd-pipeline-sa"
export SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
```

### 2. Enable Required Google Cloud APIs
```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    clouddeploy.googleapis.com \
    developerconnect.googleapis.com \
    secretmanager.googleapis.com
```

### 3. Create Custom Service Account & Grant Permissions
```bash
# Create the Service Account
gcloud iam service-accounts create $SA_NAME \
    --display-name="CI/CD Pipeline Service Account"

# Grant Artifact Registry Writer (to push images)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/artifactregistry.writer"

# Grant Cloud Deploy permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/clouddeploy.releaser"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/clouddeploy.jobRunner"

# Grant Cloud Run deploy permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/run.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/iam.serviceAccountUser"

# Grant Logging and Storage permissions (Required by Cloud Build and Cloud Deploy)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/logging.logWriter"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/storage.admin"
```

### 4. Create the Artifact Registry
```bash
gcloud artifacts repositories create demo-repo \
    --repository-format=docker \
    --location=$DEV_REGION \
    --description="Enterprise Demo Docker repo"
```

### 5. Apply Cloud Deploy Pipeline Configuration
This creates the logical pipeline connecting the Dev and Prod environments. 
*(Ensure you have updated the `clouddeploy.yaml` with your correct `$PROJECT_ID` and `$SA_EMAIL` if applying manually).*

```bash
gcloud deploy apply --file=clouddeploy.yaml --region=$DEV_REGION
```

### 6. Connect GitHub to Google Cloud
1. Go to **Developer Connect** in the Google Cloud Console.
2. Click **Create Connection** -> select **GitHub**.
3. Name it `github-conn`, choose region `us-central1`, and follow the prompts to authorize your repository.

### 7. Create the Cloud Build Trigger
1. Go to **Cloud Build > Triggers** in the console and click **Create Trigger**.
2. **Name:** `enterprise-ci-trigger`
3. **Event:** Push to branch (regex: `^main$`)
4. **Source Generation:** `2nd gen (Developer Connect)` -> Select your repo.
5. **Configuration:** `Cloud Build configuration file (yaml or json)` -> `/cloudbuild.yaml`
6. **Advanced > Service Account:** Select `CI/CD Pipeline Service Account`.
7. Click **Create**.

---

## Running the Demo

1. **Trigger a deployment:** Make a change to `src/main.py` (e.g., update the version number), commit, and push to the `main` branch.
2. **Watch the CI phase:** Open **Cloud Build > History** in the GCP console. You will see the container being built, pushed to Artifact Registry, and handed off to Cloud Deploy.
3. **Watch the CD phase:** Open **Cloud Deploy** in the console. Click `demo-app-pipeline`.
   * You will see the `dev-env` automatically deploy.
   * Verify your Dev app is live by visiting it in **Cloud Run** (`us-central1`).
4. **The Human-in-the-Loop:** Notice the pipeline is paused at `prod-env` with a **Review** button. 
5. **Promote to Prod:** Click **Review**, then **Approve**. Cloud Deploy will securely roll the exact same immutable container into your production region (`us-east1`).