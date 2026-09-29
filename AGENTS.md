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
`scholar_id`, `author_name`, and `filename` from the JSON body or query string;
`filename` and one of the other two are required.

Use `scholar_id` (the `user=` value in a Scholar profile URL). Google Scholar's
author search now redirects to a Google sign-in page, so lookups by
`author_name` fail with `StopIteration` / `MaxTriesExceededException`. That is
why the files stopped updating after 2025-05-09.

Example outputs:
- https://storage.googleapis.com/publications_scholar/ipeirotis.json
- https://storage.googleapis.com/publications_scholar/ipeirotis_pubs.json

## Layout

```
main.py                          # Cloud Function entry point: update_scholar_profile
requirements.txt                 # scholarly (pinned), bibtexparser<2, google-cloud-storage, functions-framework
.gcloudignore                    # Keeps deploy uploads to main.py + requirements.txt
monitoring/                      # Alert policy definitions (gcloud monitoring policies create --policy-from-file=...)
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
| Runtime service account | `scholar-update-runtime@scholar-pub-data.iam.gserviceaccount.com`; its only role is `roles/storage.objectAdmin` on the bucket |
| Invoker | Not public. Only `scheduler-invoker@scholar-pub-data.iam.gserviceaccount.com` has `roles/run.invoker` on the service |
| Cloud Scheduler jobs (`us-central1`) | `pubs-ipeirotis` at 03:00 (`scholar_id` `PA9La6oAAAAJ`, filename `ipeirotis`) and `pubs-foster` at 04:00 (`-Km63D4AAAAJ`, `provost`), America/New_York. Both call the function with an OIDC token for `scheduler-invoker` and retry up to 3 times, 45 minutes apart (Google Scholar intermittently blocks Cloud Run egress IPs; the spacing keeps the two jobs' retries from overlapping). They are managed with `gcloud scheduler`, not in this repo. |
| Deploy images | Artifact Registry repo `gcf-artifacts` (`us-central1`), written by each deploy. A cleanup policy keeps the 3 newest images per package and deletes untagged images older than 7 days, so only the last few revisions can be rolled back to |
| Alerting | Two Cloud Monitoring policies email the owner, both defined in `monitoring/`. "scholar-update: no successful run in 7 days" (PromQL on Cloud Run's built-in `request_count`) fires when the function has returned no HTTP 200 for a week. "scholar-update: output file older than 7 days" (log match) fires when a run fails and `log_if_stale` in `main.py` logs `SCHOLAR_UPDATE_STALE` because that job's `<filename>.json` is over 7 days old, which catches one job failing while the other works. Single failed nights are expected and do not alert. A log-based metric can't express this: PromQL alerts on those look back at most ~25h and absence conditions at most 23h30m. Log-based alert policies need `logging.notificationRules.*`, so the owner manages those. The old per-failure policy "scholar-update: nightly run failed" is disabled |
| CI deploy identity | `github@scholar-pub-data.iam.gserviceaccount.com`, key in the `GCP_SA_KEY` repo secret |

## Local development

```bash
pip install -r requirements.txt   # pins scholarly 1.7.11 + bibtexparser<2; keep both pins
pip install flake8

# Same lint checks CI runs
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Run the function locally (writes to the real bucket, so it needs GCP credentials)
functions-framework --target update_scholar_profile --debug
curl "localhost:8080/?scholar_id=PA9La6oAAAAJ&filename=test"
```

There is no test suite. Google Scholar rate-limits scraping, so avoid calling
the function in a loop.

## Deployment

Pushes to `master` run `.github/workflows/pythonapp.yml`: flake8, then
`gcloud functions deploy scholar-update --gen2 ...` using the `GCP_SA_KEY`
repository secret. Pull requests run only the lint job; they never deploy.
To deploy manually from an authenticated session:

```bash
gcloud functions deploy scholar-update --gen2 --project scholar-pub-data \
  --region us-central1 --entry-point update_scholar_profile \
  --runtime python312 --trigger-http \
  --service-account scholar-update-runtime@scholar-pub-data.iam.gserviceaccount.com
```

Never deploy with `--allow-unauthenticated`: the function takes the output
`filename` from the request, so a public endpoint lets anyone overwrite files
in the public bucket. To invoke it by hand, run one of the Scheduler jobs.

`.gcloudignore` limits the upload to `main.py` and `requirements.txt`. To check
that a deploy works end to end, run a job and look at the bucket timestamps:

```bash
gcloud scheduler jobs run pubs-ipeirotis --location us-central1
gcloud storage ls -l gs://publications_scholar/
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
| `roles/iam.serviceAccountUser` | SAs `scholar-update-runtime@…`, `scheduler-invoker@…`, and `374424129382-compute@…` only | Deploy the function as its runtime SA and edit the Scheduler jobs that use the invoker SA |
| `roles/storage.objectAdmin` | bucket `publications_scholar` only | Read/write the generated JSON files |
| `roles/artifactregistry.admin` | repo `gcf-artifacts` only | Delete old deploy images and edit the repo's cleanup policy |
| `roles/monitoring.alertPolicyEditor` | project | Create and edit metric-based alert policies. Log-based ones (`conditionMatchedLog`) also need `logging.notificationRules.*`, which the agent does not have, so the owner creates, disables or deletes those |
| `roles/monitoring.viewer` | project | Read metrics, alert policies and notification channels |

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
