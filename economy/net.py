import ipaddress
import socket

from django.conf import settings

FORWARDED_HEADERS = (
    "HTTP_FORWARDED",
    "HTTP_X_FORWARDED_FOR",
    "HTTP_X_FORWARDED_HOST",
    "HTTP_X_FORWARDED_PORT",
    "HTTP_X_FORWARDED_PROTO",
    "HTTP_X_REAL_IP",
)


def _address(value):
    try:
        return ipaddress.ip_address(value.strip())
    except (AttributeError, ValueError):
        return None


def trusted_proxy_networks():
    networks = []
    for value in settings.TRUSTED_PROXY_NETWORKS:
        try:
            networks.append(ipaddress.ip_network(value, strict=False))
        except ValueError:
            continue
    return networks


def address_in_networks(address, networks):
    parsed = _address(address)
    return bool(parsed and any(parsed in network for network in networks))


def direct_peer_is_trusted(request):
    return address_in_networks(
        request.META.get("REMOTE_ADDR", ""),
        trusted_proxy_networks(),
    )


def client_ip(request):
    remote = _address(request.META.get("REMOTE_ADDR", ""))
    if remote is None:
        return "invalid"
    networks = trusted_proxy_networks()
    if not any(remote in network for network in networks):
        return str(remote)

    header_name = settings.CLIENT_IP_HEADER
    forwarded = request.META.get(header_name, "")
    if not forwarded:
        return str(remote)
    addresses = []
    for value in forwarded.split(","):
        parsed = _address(value)
        if parsed is None:
            return str(remote)
        addresses.append(parsed)
    addresses.append(remote)
    for address in reversed(addresses):
        if not any(address in network for network in networks):
            return str(address)
    return str(addresses[0])


def parse_allowed_networks(value):
    networks = []
    errors = []
    for line in value.replace(",", "\n").splitlines():
        item = line.strip()
        if not item:
            continue
        try:
            if "/" not in item:
                address = ipaddress.ip_address(item)
                item = f"{address}/{address.max_prefixlen}"
            networks.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            errors.append(item)
    return networks, errors


def destination_ip_addresses(host, port):
    try:
        infos = socket.getaddrinfo(
            host,
            int(port),
            type=socket.SOCK_STREAM,
        )
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError("Could not resolve destination host.") from exc
    addresses = []
    seen = set()
    for info in infos:
        parsed = _address(info[4][0])
        if parsed is None:
            continue
        text = str(parsed)
        if text in seen:
            continue
        seen.add(text)
        addresses.append(parsed)
    if not addresses:
        raise ValueError("Could not resolve destination host.")
    return addresses


def require_global_destination(host, port, *, allow_private=False):
    addresses = destination_ip_addresses(host, port)
    if allow_private:
        return addresses
    for address in addresses:
        if not address.is_global:
            raise ValueError("Destination host is not a public address.")
    return addresses
