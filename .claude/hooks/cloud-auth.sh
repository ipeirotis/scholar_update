#!/bin/bash
set -e

# --- Auto-authenticate if credentials exist ---
CONFIG=".cloud-config.json"
if [ ! -f "$CONFIG" ]; then exit 0; fi

PROVIDER=$(jq -r .provider "$CONFIG" 2>/dev/null) || exit 0
if [ "$PROVIDER" != "gcp" ]; then exit 0; fi

USER_EMAIL=$(git config user.email 2>/dev/null || true)
ENC_FILE=".cloud-credentials.${USER_EMAIL}.enc"
if [ -z "$USER_EMAIL" ] || [ ! -f "$ENC_FILE" ]; then exit 0; fi

KEY="${GCP_CREDENTIALS_KEY:-$CLOUD_CREDENTIALS_KEY}"
if [ -z "$KEY" ]; then exit 0; fi

# --- Drop the sandbox's placeholder gcloud token ---
# The Claude Code on the Web container exports CLOUDSDK_AUTH_ACCESS_TOKEN set to
# a proxy placeholder. gcloud gives that variable precedence over any activated
# account, so every call fails with 401 until it is unset (here and, via
# $CLAUDE_ENV_FILE below, for the rest of the session).
unset CLOUDSDK_AUTH_ACCESS_TOKEN

# --- Install gcloud if missing ---
if ! command -v gcloud &> /dev/null; then
  for dir in /home/user/google-cloud-sdk/bin /usr/lib/google-cloud-sdk/bin /usr/local/google-cloud-sdk/bin; do
    if [ -x "$dir/gcloud" ]; then export PATH="$dir:$PATH"; break; fi
  done
fi
if ! command -v gcloud &> /dev/null; then
  INSTALLER=$(curl -sSL https://sdk.cloud.google.com 2>/dev/null) || true
  if [ -z "$INSTALLER" ] || ! echo "$INSTALLER" | bash -s -- --disable-prompts --install-dir=/home/user; then
    echo "WARNING: gcloud SDK install failed — skipping GCP auth."
    exit 0
  fi
  export PATH="/home/user/google-cloud-sdk/bin:$PATH"
fi

# --- Decrypt credentials to a session-stable, private location ---
# The decrypted key must persist for the whole session so that Python Google
# client libraries (which read GOOGLE_APPLICATION_CREDENTIALS / ADC, not the
# gcloud CLI auth store) can authenticate. It lives only in the ephemeral
# sandbox, never in the repo (the repo only ever holds the encrypted .enc).
ADC_KEY="/tmp/gcp-adc-credentials.json"
if ! (umask 077 && echo "$KEY" | openssl enc -d -aes-256-cbc -pbkdf2 \
  -pass stdin -in "$ENC_FILE" -out "$ADC_KEY" 2>/dev/null); then
  echo "WARNING: Failed to decrypt credentials — check GCP_CREDENTIALS_KEY or .enc file integrity."
  rm -f "$ADC_KEY"
  exit 0
fi

if ! gcloud auth activate-service-account --key-file="$ADC_KEY" 2>/dev/null; then
  echo "WARNING: gcloud auth failed — credentials may be revoked."
  rm -f "$ADC_KEY"
  exit 0
fi
gcloud config set project "$(jq -r .project_id "$CONFIG" 2>/dev/null)" 2>/dev/null || true

# --- Populate Application Default Credentials for Python client libraries ---
export GOOGLE_APPLICATION_CREDENTIALS="$ADC_KEY"

# --- Persist gcloud PATH + ADC env for the rest of the session ---
# SessionStart runs in a short-lived subprocess; without persisting these,
# later commands in the session would not find gcloud or have ADC set.
# $CLAUDE_ENV_FILE is the harness mechanism for exporting env to the session
# (the same approach this skill's AWS hook uses for its credentials).
if [ -n "$CLAUDE_ENV_FILE" ]; then
  GCLOUD_BIN="$(dirname "$(command -v gcloud)")"
  grep -qxF "export PATH=\"$GCLOUD_BIN:\$PATH\"" "$CLAUDE_ENV_FILE" 2>/dev/null || \
    echo "export PATH=\"$GCLOUD_BIN:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  grep -qxF "export GOOGLE_APPLICATION_CREDENTIALS=\"$ADC_KEY\"" "$CLAUDE_ENV_FILE" 2>/dev/null || \
    echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$ADC_KEY\"" >> "$CLAUDE_ENV_FILE"
  grep -qxF "unset CLOUDSDK_AUTH_ACCESS_TOKEN" "$CLAUDE_ENV_FILE" 2>/dev/null || \
    echo "unset CLOUDSDK_AUTH_ACCESS_TOKEN" >> "$CLAUDE_ENV_FILE"
fi

echo "GCP credentials activated for $USER_EMAIL (gcloud CLI + Python ADC)"
