#!/usr/bin/env bash
# Envia un evento del pipeline CI/CD a OpenObserve (API HTTP/JSON).
# Uso: send_o2_event.sh <event_type> <status> [detalle]
#   event_type: tests | deploy | deploy_blocked
#   status:     success | failure | cancelled | blocked
# Variables requeridas: O2_URL, O2_USER, O2_PASSWORD (secrets de GitHub)
set -uo pipefail

EVENT_TYPE="${1:?event_type requerido}"
STATUS="${2:?status requerido}"
DETAIL="${3:-}"
ORG="${O2_ORG:-default}"
STREAM="${O2_STREAM:-cicd_pipeline}"

if [ -z "${O2_URL:-}" ]; then
  echo "::warning::O2_URL no configurado; no se envia el evento a OpenObserve"
  exit 0
fi

PAYLOAD=$(jq -n \
  --arg event_type "$EVENT_TYPE" \
  --arg status "$STATUS" \
  --arg detail "$DETAIL" \
  --arg commit_sha "${GITHUB_SHA:-}" \
  --arg commit_short "${GITHUB_SHA:0:7}" \
  --arg commit_message "${COMMIT_MESSAGE:-}" \
  --arg branch "${GITHUB_REF_NAME:-}" \
  --arg actor "${GITHUB_ACTOR:-}" \
  --arg repository "${GITHUB_REPOSITORY:-}" \
  --arg workflow "${GITHUB_WORKFLOW:-}" \
  --arg trigger "${GITHUB_EVENT_NAME:-}" \
  --arg run_id "${GITHUB_RUN_ID:-}" \
  --arg run_number "${GITHUB_RUN_NUMBER:-}" \
  --arg run_url "${GITHUB_SERVER_URL:-}/${GITHUB_REPOSITORY:-}/actions/runs/${GITHUB_RUN_ID:-}" \
  --arg pytest "${PYTEST_OUTCOME:-}" \
  --arg jest "${JEST_OUTCOME:-}" \
  --arg playwright "${PLAYWRIGHT_OUTCOME:-}" \
  --arg target_host "${EC2_HOST:-}" \
  '[{event_type:$event_type, status:$status, detail:$detail,
     commit_sha:$commit_sha, commit_short:$commit_short, commit_message:$commit_message,
     branch:$branch, actor:$actor, repository:$repository, workflow:$workflow,
     trigger:$trigger, run_id:$run_id, run_number:$run_number, run_url:$run_url,
     pytest_result:$pytest, jest_result:$jest, playwright_result:$playwright,
     target_host:$target_host}]')

echo "Enviando a OpenObserve ($STREAM): $PAYLOAD"
curl -sS --max-time 15 --fail-with-body \
  -u "${O2_USER}:${O2_PASSWORD}" \
  -H "Content-Type: application/json" \
  -X POST "${O2_URL%/}/api/${ORG}/${STREAM}/_json" \
  -d "$PAYLOAD" \
  || echo "::warning::No se pudo enviar el evento a OpenObserve"
echo
