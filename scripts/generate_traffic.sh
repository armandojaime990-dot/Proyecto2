#!/usr/bin/env bash
# Genera trafico contra la app para poblar las graficas de OpenObserve.
# Uso: bash scripts/generate_traffic.sh http://TU_IP_EC2 [vueltas]
set -u
BASE="${1:?Uso: generate_traffic.sh http://IP [vueltas]}"
ROUNDS="${2:-100}"
EMAIL="${ADMIN_EMAIL:-admin@demo.com}"
PASS="${ADMIN_PASSWORD:-Admin123!}"

for i in $(seq 1 "$ROUNDS"); do
  TOKEN=$(curl -s -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')
  H="Authorization: Bearer $TOKEN"
  curl -s -o /dev/null "$BASE/api/health"
  curl -s -o /dev/null -H "$H" "$BASE/api/users"
  ID=$(curl -s -X POST "$BASE/api/users" -H "$H" -H 'Content-Type: application/json' \
    -d "{\"name\":\"Carga $i\",\"email\":\"carga$i.$RANDOM@test.com\",\"password\":\"secreto1\",\"role\":\"user\"}" \
    | sed -n 's/.*"id":\([0-9]*\).*/\1/p')
  curl -s -o /dev/null -H "$H" "$BASE/api/users/$ID"
  curl -s -o /dev/null -X PUT -H "$H" -H 'Content-Type: application/json' -d '{"name":"Carga editada"}' "$BASE/api/users/$ID"
  curl -s -o /dev/null -X DELETE -H "$H" "$BASE/api/users/$ID"
  # errores intencionales (4xx) para la grafica de tasa de error
  curl -s -o /dev/null -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' -d '{"email":"x@x.com","password":"mal"}'
  curl -s -o /dev/null -H "$H" "$BASE/api/users/999999"
  curl -s -o /dev/null "$BASE/api/users"
  echo "Vuelta $i/$ROUNDS"
done
