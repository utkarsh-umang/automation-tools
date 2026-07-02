#!/bin/bash
set -e

# ── Config — fill these in once ───────────────────────────────────────────────
REGISTRY="us-central1-docker.pkg.dev/enlead-ai/automation-tools"
VM_USER="utk_umang"
VM_IP="34.68.94.96"
VM_DIR="~/automation-tools"
COMPOSE_FILE="docker-compose.prod.yml"
# Immutable per-deploy tag so every pushed image is traceable to a commit and
# can be rolled back to. Falls back to a timestamp if not in a git checkout.
TAG="$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
# ──────────────────────────────────────────────────────────────────────────────

BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
RESET="\033[0m"

log() { echo -e "${CYAN}▶ $1${RESET}"; }
success() { echo -e "${GREEN}✓ $1${RESET}"; }

# Copy the latest compose + nginx config to the VM so they stay in sync
sync_compose() {
    log "Syncing $COMPOSE_FILE and nginx.conf to VM..."
    gcloud compute scp "$COMPOSE_FILE" "${VM_USER}@tools-automation:${VM_DIR}/${COMPOSE_FILE}" \
        --zone=us-central1-c --project=enlead-ai
    gcloud compute scp ./frontend/nginx.conf "${VM_USER}@tools-automation:${VM_DIR}/nginx.conf" \
        --zone=us-central1-c --project=enlead-ai
    success "Compose file and nginx.conf synced"
}

deploy_backend() {
    log "Building backend image (tag: latest + ${TAG})..."
    docker build --platform linux/amd64 -t "$REGISTRY/backend:latest" -t "$REGISTRY/backend:${TAG}" ./backend-app -f ./backend-app/Dockerfile

    log "Building celery-worker image (tag: latest + ${TAG})..."
    docker build --platform linux/amd64 -t "$REGISTRY/celery-worker:latest" -t "$REGISTRY/celery-worker:${TAG}" ./backend-app -f ./backend-app/Dockerfile.celery

    log "Pushing backend images..."
    docker push "$REGISTRY/backend:latest" && docker push "$REGISTRY/backend:${TAG}"
    docker push "$REGISTRY/celery-worker:latest" && docker push "$REGISTRY/celery-worker:${TAG}"

    sync_compose

    log "Restarting backend + celery-worker + celery-beat on VM..."
    gcloud compute ssh "${VM_USER}@tools-automation" --zone=us-central1-c --project=enlead-ai -- \
        "cd ${VM_DIR} && docker compose -f ${COMPOSE_FILE} pull backend celery-worker celery-beat && docker compose -f ${COMPOSE_FILE} up -d backend celery-worker celery-beat"

    success "Backend deployed"
}

deploy_frontend() {
    log "Building frontend image (tag: latest + ${TAG})..."
    docker build --platform linux/amd64 -t "$REGISTRY/frontend:latest" -t "$REGISTRY/frontend:${TAG}" ./frontend -f ./frontend/Dockerfile

    log "Pushing frontend image..."
    docker push "$REGISTRY/frontend:latest" && docker push "$REGISTRY/frontend:${TAG}"

    sync_compose

    log "Restarting frontend on VM..."
    gcloud compute ssh "${VM_USER}@tools-automation" --zone=us-central1-c --project=enlead-ai -- \
        "cd ${VM_DIR} && docker compose -f ${COMPOSE_FILE} pull frontend && docker compose -f ${COMPOSE_FILE} up -d frontend"

    success "Frontend deployed"
}

# ── Menu ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Deployment options:${RESET}"
echo "  1) Backend only  (backend + celery-worker)"
echo "  2) Frontend only"
echo "  3) Full deploy   (backend + frontend)"
echo ""
read -rp "Select option [1-3]: " option

case $option in
    1)
        deploy_backend
        ;;
    2)
        deploy_frontend
        ;;
    3)
        deploy_backend
        deploy_frontend
        ;;
    *)
        echo "Invalid option. Please enter 1, 2, or 3."
        exit 1
        ;;
esac

echo ""
success "Done! App is live at https://tools.scalebrandslab.com"
