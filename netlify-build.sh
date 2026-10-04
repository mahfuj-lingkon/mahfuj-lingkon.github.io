#!/usr/bin/env bash
# Builds the Hugo site, downloading Hugo first if it isn't on the PATH.
set -euo pipefail

HUGO_VERSION="${HUGO_VERSION:-0.167.0}"

if ! command -v hugo >/dev/null 2>&1; then
  HUGO_DIR="${NETLIFY_CACHE_DIR:-/tmp}/hugo-${HUGO_VERSION}"
  if [ ! -x "${HUGO_DIR}/hugo" ]; then
    echo "Installing Hugo extended ${HUGO_VERSION}"
    mkdir -p "${HUGO_DIR}"
    curl -fsSL "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz" \
      | tar -xz -C "${HUGO_DIR}" hugo
  fi
  export PATH="${HUGO_DIR}:${PATH}"
fi

hugo version
hugo --gc --minify
