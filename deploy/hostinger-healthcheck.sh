#!/bin/sh
set -eu

profile=hostinger-caddy-v1
project_root=${1:-/opt/kinkudos}
deploy_dir="$project_root/deploy"
profile_file="$project_root/install-profile"

fail() {
  echo "State: failed"
  echo "$*" >&2
  docker compose logs --tail=60 app caddy >&2 2>/dev/null || true
  exit 1
}

[ -f "$profile_file" ] && [ "$(cat "$profile_file")" = "$profile" ] \
  || { echo "State: failed"; echo "Unsupported or missing installation profile." >&2; exit 1; }
cd "$deploy_dir"
hostname=$(sed -n 's/^KINKUDOS_HOSTNAME=//p' .env | tail -n 1)
[ -n "$hostname" ] || fail "KINKUDOS_HOSTNAME is missing."

attempt=0
app_healthy=false
while [ "$attempt" -lt 60 ]; do
  app_container=$(docker compose ps -q app 2>/dev/null || true)
  app_status=$(docker inspect "$app_container" \
    --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
    2>/dev/null || true)
  if [ "$app_status" = healthy ]; then
    app_healthy=true
    break
  fi
  attempt=$((attempt + 1))
  sleep 2
done
[ "$app_healthy" = true ] || fail "The KinKudos application did not become healthy."

caddy_container=$(docker compose ps -q caddy 2>/dev/null || true)
caddy_running=$(docker inspect "$caddy_container" --format '{{.State.Running}}' 2>/dev/null || true)
[ "$caddy_running" = true ] || fail "Caddy is not running."

http_status=$(curl --silent --output /dev/null --write-out '%{http_code}' --max-time 10 \
  --resolve "$hostname:80:127.0.0.1" "http://$hostname/setup/" 2>/dev/null || true)
case "$http_status" in
  301|302|307|308) ;;
  *) fail "Caddy did not redirect HTTP to HTTPS." ;;
esac

wait_seconds=${KINKUDOS_HTTPS_WAIT_SECONDS:-180}
attempt=0
while [ "$attempt" -lt "$wait_seconds" ]; do
  if curl --fail --silent --show-error --max-time 10 \
    --resolve "$hostname:443:127.0.0.1" "https://$hostname/setup/" >/dev/null 2>&1; then
    echo "State: deployed and HTTPS ready"
    echo "HTTPS is ready: https://$hostname/setup/"
    exit 0
  fi
  attempt=$((attempt + 5))
  sleep 5
done

echo "State: deployed but HTTPS pending"
echo "KinKudos and Caddy are running, but DNS propagation or ACME issuance is still pending."
echo "Confirm that DNS points to this VPS and Hostinger allows inbound TCP 80 and 443."
echo "Retry: $deploy_dir/hostinger-healthcheck.sh $project_root"
exit 2
