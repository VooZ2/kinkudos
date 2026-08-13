#!/bin/sh
# Resolve and persist KINKUDOS_TRUSTED_PROXIES for guided setup and upgrades.
# Does not overwrite a non-empty value already present in the env file.
set -eu

usage() {
  echo "Usage: ensure-trusted-proxies.sh ENV_FILE [PROXY_MODE] [PROXY_NETWORK]" >&2
  exit 2
}

env_file=${1:-}
explicit_proxy_mode=${2:-}
explicit_proxy_network=${3:-}
if [ -z "$env_file" ]; then
  usage
fi
if [ ! -f "$env_file" ]; then
  echo "Environment file was not found: $env_file" >&2
  exit 1
fi

read_env_value() {
  # Prefer the last assignment so later operator edits win.
  sed -n "s/^${1}=//p" "$env_file" | tail -n 1
}

existing_trusted=$(read_env_value KINKUDOS_TRUSTED_PROXIES)
if [ -n "$existing_trusted" ]; then
  exit 0
fi

install_language=$(read_env_value KINKUDOS_DEFAULT_LANGUAGE)
install_language=${install_language:-en}

infer_proxy_mode_from_override() {
  override_file=$(CDPATH= cd -- "$(dirname -- "$env_file")" && pwd)/compose.override.yml
  if [ ! -f "$override_file" ]; then
    return 0
  fi
  if grep -q 'traefik\.' "$override_file"; then
    printf '%s\n' traefik
    return 0
  fi
  if grep -q '127\.0\.0\.1:.*:8000' "$override_file"; then
    printf '%s\n' host
    return 0
  fi
  if grep -q 'external:[[:space:]]*true' "$override_file"; then
    printf '%s\n' container
    return 0
  fi
}

proxy_mode=${explicit_proxy_mode:-${KINKUDOS_PROXY_MODE:-$(read_env_value KINKUDOS_PROXY_MODE)}}
if [ -z "$proxy_mode" ]; then
  proxy_mode=$(infer_proxy_mode_from_override || true)
fi
proxy_mode=${proxy_mode:-host}
case "$proxy_mode" in
  host|traefik|container) ;;
  *)
    echo "Proxy mode must be host, traefik, or container." >&2
    exit 1
    ;;
esac

# Persist inferred/selected mode so later upgrades stay consistent.
if ! grep -q '^KINKUDOS_PROXY_MODE=' "$env_file"; then
  printf 'KINKUDOS_PROXY_MODE=%s\n' "$proxy_mode" >> "$env_file"
fi

default_proxy_network=web
if [ "$proxy_mode" = "container" ]; then
  default_proxy_network=proxy
fi
proxy_network=${explicit_proxy_network:-${KINKUDOS_PROXY_NETWORK:-$(read_env_value KINKUDOS_PROXY_NETWORK)}}
proxy_network=${proxy_network:-$default_proxy_network}
if [ "$proxy_mode" != "host" ] && ! grep -q '^KINKUDOS_PROXY_NETWORK=' "$env_file"; then
  printf 'KINKUDOS_PROXY_NETWORK=%s\n' "$proxy_network" >> "$env_file"
fi

validate_cidrs() {
  value=$1
  python3 - "$value" <<'PY'
import ipaddress
import sys

raw = sys.argv[1].strip()
if not raw:
    raise SystemExit(1)
for part in raw.split(","):
    item = part.strip()
    if not item:
        raise SystemExit(1)
    ipaddress.ip_network(item, strict=False)
PY
}

write_trusted_proxies() {
  value=$(printf '%s' "$1" | tr -d '\n\r')
  if [ -z "$value" ]; then
    echo "Trusted proxy value must be a non-empty single line." >&2
    exit 1
  fi
  if ! validate_cidrs "$value"; then
    echo "Invalid trusted proxy CIDR list: $value" >&2
    exit 1
  fi
  temporary_env=$(mktemp "${env_file}.trusted.XXXXXX")
  grep -v -E '^KINKUDOS_TRUSTED_PROXIES=' "$env_file" > "$temporary_env" || true
  printf 'KINKUDOS_TRUSTED_PROXIES=%s\n' "$value" >> "$temporary_env"
  chmod 0600 "$temporary_env"
  mv "$temporary_env" "$env_file"
}

prompt_manual_cidr() {
  if [ "$install_language" = "lt" ]; then
    printf "Diegimas sustabdytas: proxy režimui '%s' reikia KINKUDOS_TRUSTED_PROXIES,\n" "$proxy_mode" >&2
    printf "bet Docker tinklas '%s' nerastas (arba neturi subneto),\n" "$proxy_network" >&2
    printf "todėl CIDR negalima nustatyti automatiškai.\n" >&2
    printf "Padarykite vieną iš šių veiksmų ir paleiskite iš naujo:\n" >&2
    printf "  1) sukurkite tinklą: docker network create %s\n" "$proxy_network" >&2
    printf "  2) arba įrašykite į deploy/.env, pvz.:\n" >&2
    printf "     KINKUDOS_TRUSTED_PROXIES=172.18.0.0/16\n" >&2
    printf "  3) arba pataisykite KINKUDOS_PROXY_NETWORK į tikrą proxy tinklo vardą.\n" >&2
  else
    printf "Setup stopped: proxy mode '%s' requires KINKUDOS_TRUSTED_PROXIES,\n" "$proxy_mode" >&2
    printf "but Docker network '%s' was not found (or has no subnet),\n" "$proxy_network" >&2
    printf "so the CIDR could not be set automatically.\n" >&2
    printf "Do one of the following, then retry:\n" >&2
    printf "  1) create the network: docker network create %s\n" "$proxy_network" >&2
    printf "  2) or set it in deploy/.env, for example:\n" >&2
    printf "     KINKUDOS_TRUSTED_PROXIES=172.18.0.0/16\n" >&2
    printf "  3) or fix KINKUDOS_PROXY_NETWORK to your real proxy network name.\n" >&2
  fi
  if [ ! -t 0 ]; then
    exit 1
  fi
  if [ "$install_language" = "lt" ]; then
    printf "Arba įveskite proxy tinklo CIDR dabar:\n" >&2
  else
    printf "Or enter the proxy network CIDR now:\n" >&2
  fi
  printf '> '
  read -r manual_cidr
  manual_cidr=${manual_cidr:-}
  if [ -z "$manual_cidr" ]; then
    if [ "$install_language" = "lt" ]; then
      echo "Tuščia reikšmė. Diegimas sustabdytas — nustatykite KINKUDOS_TRUSTED_PROXIES ir bandykite dar kartą." >&2
    else
      echo "Empty value. Setup stopped — set KINKUDOS_TRUSTED_PROXIES and retry." >&2
    fi
    exit 1
  fi
  write_trusted_proxies "$manual_cidr"
}

docker_network_subnets() {
  network_name=$1
  if ! command -v docker >/dev/null 2>&1; then
    return 1
  fi
  if ! docker network inspect "$network_name" >/dev/null 2>&1; then
    return 1
  fi
  docker network inspect "$network_name" \
    --format '{{range .IPAM.Config}}{{if .Subnet}}{{.Subnet}} {{end}}{{end}}' \
    | tr -s '[:space:]' '\n' \
    | sed '/^$/d' \
    | awk 'NR > 1 { printf "," } { printf "%s", $0 } END { if (NR) printf "\n" }'
}

# Environment override for non-interactive installs (do not invent a value).
if [ -n "${KINKUDOS_TRUSTED_PROXIES:-}" ]; then
  write_trusted_proxies "$KINKUDOS_TRUSTED_PROXIES"
  exit 0
fi

if [ "$proxy_mode" = "host" ]; then
  write_trusted_proxies "127.0.0.0/8,::1/128"
  exit 0
fi

# Docker reverse proxies (Traefik / NPM / container Caddy) peer from the
# shared Docker network, not from loopback.
subnets=$(docker_network_subnets "$proxy_network" || true)
subnets=$(printf '%s' "$subnets" | tr -d '\n\r')
if [ -n "$subnets" ]; then
  write_trusted_proxies "$subnets"
  exit 0
fi

prompt_manual_cidr
