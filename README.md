# agentactioncapsule-site

Static site for **agentactioncapsule.org** — the neutral IETF standard page for the Agent Action
Capsule profile, plus the HashiCorp-style concept/docs layer.

Self-contained HTML, served by nginx:alpine on port 8080. **No build step at deploy** — the docs
pages are pre-generated static files.

```
index.html              The standard landing (apex)
docs/index.html         Docs overview
docs/*.html             8 concept/guide/reference pages
tools/build_docs.py     Docs generator (authoring-time only; emits docs/*.html)
Dockerfile, nginx.conf  nginx:alpine static container, port 8080
robots.txt, sitemap.xml
LICENSE, NOTICE         Apache-2.0
```

Neutral substrate: documents the open specification and the open-source implementations only;
no product or business content. The three neutral surfaces (this site,
`anchor.agentactioncapsule.org`, `verify.agentactioncapsule.org`) share one visual system and a common
cross-site nav + footer.

## Run locally

```sh
docker build -t agentactioncapsule-site .
docker run --rm -p 8080:8080 agentactioncapsule-site
curl -I http://localhost:8080/            # 200
curl -I http://localhost:8080/docs/       # 200
curl -I http://localhost:8080/docs/glossary.html   # 200
```

## Editing the docs

Edit content in `tools/build_docs.py` (the `PAGES` dict + `INDEX_BODY`), then regenerate:

```sh
python3 tools/build_docs.py     # rewrites docs/*.html
```

## Automated deploy

`.github/workflows/deploy.yml` deploys to Cloud Run automatically on every push to `main`, so
"merged" always means "live". The deploy job is gated on `neutrality-gate` (a self-contained
re-run of the same reserved-vocabulary scan the PR gate runs) — it never runs if that scan fails
or the `NEUTRALITY_TERMS` secret is missing, so a direct push to `main` that bypassed PR review
still cannot ship non-neutral content.

Auth is keyless **Workload Identity Federation** via `google-github-actions/auth@v2` — no
long-lived service-account key is stored in this repo. This requires a **one-time GCP setup**,
gated to whoever holds `fluxxom` project admin (Steven). The workflow only consumes the result;
it does not create or touch any of the following.

**1. Enable the required APIs:**

```sh
gcloud services enable \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project fluxxom
```

**2. Create a Workload Identity Pool + Provider bound to this repo:**

```sh
gcloud iam workload-identity-pools create "github-actions" \
  --project fluxxom \
  --location global \
  --display-name "GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc "agentactioncapsule-web" \
  --project fluxxom \
  --location global \
  --workload-identity-pool "github-actions" \
  --display-name "agentactioncapsule-web" \
  --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition "assertion.repository=='action-state-group/agentactioncapsule-web'" \
  --issuer-uri "https://token.actions.githubusercontent.com"
```

**3. Create the deploy service account and grant it the roles it needs to source-deploy to Cloud
Run:**

```sh
gcloud iam service-accounts create "deploy-agentactioncapsule-site" \
  --project fluxxom \
  --display-name "Cloud Run deploy — agentactioncapsule-site"

SA="deploy-agentactioncapsule-site@fluxxom.iam.gserviceaccount.com"

for role in roles/run.admin roles/iam.serviceAccountUser roles/cloudbuild.builds.editor \
            roles/artifactregistry.writer roles/logging.viewer; do
  gcloud projects add-iam-policy-binding fluxxom \
    --member "serviceAccount:${SA}" \
    --role "${role}"
done
```

**4. Allow the GitHub repo (via the WIF pool) to impersonate that service account:**

```sh
PROJECT_NUMBER=$(gcloud projects describe fluxxom --format='value(projectNumber)')

gcloud iam service-accounts add-iam-policy-binding "${SA}" \
  --project fluxxom \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/attribute.repository/action-state-group/agentactioncapsule-web"
```

**5. Add repo variables** (Settings → Secrets and variables → Actions → Variables — these are
resource identifiers, not secrets):

- `GCP_WIF_PROVIDER` — full provider resource name, from:
  ```sh
  gcloud iam workload-identity-pools providers describe "agentactioncapsule-web" \
    --project fluxxom --location global \
    --workload-identity-pool "github-actions" --format='value(name)'
  ```
- `GCP_DEPLOY_SA_EMAIL` — `deploy-agentactioncapsule-site@fluxxom.iam.gserviceaccount.com`

Confirm the `NEUTRALITY_TERMS` secret (already required by `neutrality.yml`) is set — the deploy
gate depends on it too.

## Manual deploy (break-glass fallback, gated — Steven only)

```sh
# from this directory:
gcloud run deploy agentactioncapsule-site \
  --project fluxxom \
  --region us-central1 \
  --source . \
  --allow-unauthenticated

# map the apex domain (already verified in fluxxom):
gcloud beta run domain-mappings create \
  --service agentactioncapsule-site \
  --domain agentactioncapsule.org \
  --region us-central1 \
  --project fluxxom
```

After the domain mapping, Google returns A/AAAA records (`rrdata`). Add those as **A** and **AAAA**
records for `agentactioncapsule.org` in Bluehost DNS (no www needed for the apex mapping). HTTPS
cert is auto-provisioned once DNS resolves.

> Repo-name note: the brief calls the public repo `agentactioncapsule-web`; this staging folder and
> the Cloud Run **service** are named `agentactioncapsule-site` (from the earlier Part-2 work). The
> service name and the GitHub repo name don't have to match — confirm the GitHub repo name at
> creation time.

## Standards status

`draft-mih-scitt-agent-action-capsule` is an **individual** IETF Internet-Draft — not WG-adopted,
not a standard. The SCITT substrate it builds on is now published: the SCITT Architecture is
**RFC 9943** and COSE Receipts are **RFC 9942** (both June 2026); RFC 9162 is also a published RFC.
(The COSE Merkle Tree Proofs wire format — `draft-ietf-cose-merkle-tree-proofs` — remains an
Internet-Draft.)

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
