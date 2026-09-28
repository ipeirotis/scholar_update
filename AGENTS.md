# AGENTS.md

Guidance for coding agents working in this repository.

## What this repo does

`main.py` is an HTTP Google Cloud Function (gen2) that scrapes a Google Scholar
profile with the [`scholarly`](https://github.com/scholarly-python-package/scholarly)
library and writes two JSON files to a public GCS bucket:

- `<filename>.json` — the author profile (without the publications list)
- `<filename>_pubs.json` — the publications list, with `num_citations`
  renamed to `citedby`

Both files get `last_updated` / `last_updated_ts` fields. The function takes
`author_name` and `filename` from the JSON body or query string.

Example outputs:
- https://storage.googleapis.com/publications_scholar/ipeirotis.json
- https://storage.googleapis.com/publications_scholar/ipeirotis_pubs.json

## Layout

```
main.py                          # Cloud Function entry point: update_scholar_profile
requirements.txt                 # scholarly, google-cloud-storage
.github/workflows/pythonapp.yml  # flake8 lint, then gcloud functions deploy
.claude/skills/cloud-bootstrap/  # Skill that manages encrypted GCP credentials
```

## Google Cloud resources

| Resource | Value |
|---|---|
| Project | `scholar-pub-data` |
| Region | `us-central1` |
| Cloud Function (gen2, HTTP) | `scholar-update`, entry point `update_scholar_profile` |
| GCS bucket (public read) | `publications_scholar` (hard-coded in `store_data_on_bucket`) |
| Runtime service account | `374424129382-compute@developer.gserviceaccount.com` (default compute SA) |
| Cloud Scheduler jobs (`us-central1`) | `pubs-ipeirotis` at 03:00 and `pubs-foster` at 04:00, America/New_York. They already exist; the creation commands in the workflow are commented out. |
| CI deploy identity | `github@scholar-pub-data.iam.gserviceaccount.com`, key in the `GCP_SA_KEY` repo secret |

## Local development

```bash
pip install -r requirements.txt
pip install flake8 functions-framework

# Same lint checks CI runs
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run the function locally (writes to the real bucket, so it needs GCP credentials)
functions-framework --target update_scholar_profile --debug
curl "localhost:8080/?author_name=ipeirotis&filename=test"
```

There is no test suite. Google Scholar rate-limits scraping, so avoid calling
the function in a loop.

## Deployment

Pushes to `master` run `.github/workflows/pythonapp.yml`: flake8, then
`gcloud functions deploy scholar-update --gen2 ...` using the `GCP_SA_KEY`
repository secret. To deploy manually from an authenticated session:

```bash
gcloud functions deploy scholar-update --gen2 --project scholar-pub-data \
  --region us-central1 --entry-point update_scholar_profile \
  --runtime python38 --trigger-http
```

## Conventions

- Keep `main.py` a single-file function; Cloud Functions deploys the repo root.
- Match the existing style: 4-space indent, lines ≤ 127 characters (flake8 config in CI).
- Never commit plaintext credentials (`credentials.json`, service-account keys).

## Cloud Credentials

This repo uses the `cloud-bootstrap` skill (`.claude/skills/cloud-bootstrap/`,
v1.4.0) to keep encrypted GCP service-account keys in the repo, so agent
sessions can authenticate to `scholar-pub-data` without pasting credentials.

- **Provider / project:** GCP, `scholar-pub-data` (config in `.cloud-config.json`)
- **Service account:** `claude-agent@scholar-pub-data.iam.gserviceaccount.com`

Roles granted:

| Role | Scope | Why |
|---|---|---|
| `roles/cloudfunctions.developer` | project | Deploy/update `scholar-update`; includes invoking it and `projects.get` |
| `roles/cloudscheduler.admin` | project | Create, edit, and run the daily Scheduler jobs |
| `roles/logging.viewer` | project | Read function logs when debugging |
| `roles/iam.serviceAccountUser` | runtime SA `374424129382-compute@…` only | Required to deploy a function (or Scheduler job) that runs as that SA |
| `roles/storage.objectAdmin` | bucket `publications_scholar` only | Read/write the generated JSON files |

**Multi-user setup.** Each team member has their own key, encrypted with their
own passphrase, in `.cloud-credentials.<git-email>.enc`. Passphrases live only
in the Claude Code on the Web environment variable `GCP_CREDENTIALS_KEY` (or
`CLOUD_CREDENTIALS_KEY`), never in the repo.

**Authentication** is automatic: `.claude/hooks/cloud-auth.sh` runs at
SessionStart (configured in `.claude/settings.json`), installs `gcloud` if
needed, decrypts the key to `/tmp/gcp-adc-credentials.json`, activates it for
`gcloud`, and exports `GOOGLE_APPLICATION_CREDENTIALS` for Python clients. It
also unsets the sandbox's placeholder `CLOUDSDK_AUTH_ACCESS_TOKEN`, which
otherwise overrides the activated account and makes every `gcloud` call fail
with 401. If auth is missing mid-session, use the skill's `authenticate`
workflow.

**New team members:** open the repo in Claude Code on the Web with their own
passphrase set and ask to be added to cloud access. The skill's
`add-team-member` workflow creates a new key for the same service account (GCP
allows 10 keys per SA).

**More permissions:** on a 403, follow the skill's `permission-escalation`
workflow. The agent proposes the narrowest role and a human grants it; the
agent never edits IAM on its own. Keys older than 180 days trigger the
`credential-rotation` workflow.
