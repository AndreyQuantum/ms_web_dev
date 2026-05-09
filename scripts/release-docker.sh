#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?usage: release-docker.sh <version>}"
REPO_LOWER="${GITHUB_REPOSITORY,,}"
REGISTRY_BASE="ghcr.io/${REPO_LOWER}"

SERVICES=(products_microservice orders_microservice)

for SERVICE in "${SERVICES[@]}"; do
  IMAGE="${REGISTRY_BASE}/${SERVICE}"
  echo ">>> Building & pushing ${IMAGE} (${VERSION}, latest)"
  docker buildx build \
    --tag "${IMAGE}:${VERSION}" \
    --tag "${IMAGE}:latest" \
    --cache-from "type=gha,scope=${SERVICE}" \
    --cache-to "type=gha,mode=max,scope=${SERVICE}" \
    --push \
    "./${SERVICE}"
done
