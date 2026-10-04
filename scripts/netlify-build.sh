#!/usr/bin/env bash
# Builds the site on Netlify, installing Hugo first if it isn't already available.
set -euo pipefail

HUGO_VERSION="${HUGO_VERSION:-0.167.0}"

if ! command -v hugo >/dev/null 2>&1; then
  echo "Hugo not found; installing Hugo extended v${HUGO_VERSION}"
  HUGO_DIR="${HOME}/.cache/hugo/${HUGO_VERSION}"
  mkdir -p "${HUGO_DIR}"
  if [ ! -x "${HUGO_DIR}/hugo" ]; then
    curl -fsSL "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz" \
      | tar -xz -C "${HUGO_DIR}" hugo
  fi
  export PATH="${HUGO_DIR}:${PATH}"
fi

hugo version

if [ -n "${DEPLOY_PRIME_URL:-}" ]; then
  hugo --gc --minify -b "${DEPLOY_PRIME_URL}/"
else
  hugo --gc --minify
fi
