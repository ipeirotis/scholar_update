#!/bin/sh

# Decrypt the file
gpg --quiet --batch --yes --decrypt --passphrase="$GPG_PASSWORD" \
--output $HOME/google-credentials-scholarAPI.json google-credentials-scholarAPI.json.gpg
