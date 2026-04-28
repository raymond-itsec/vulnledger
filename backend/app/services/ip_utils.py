import ipaddress

from fastapi import Request


def parse_ip_candidate(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    # Handle potential "IP:port" form from some proxies.
    if candidate.count(":") == 1 and "." in candidate:
        host, _, _ = candidate.partition(":")
        candidate = host.strip()
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def extract_forwarded_ips(request: Request) -> list[str]:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if not forwarded_for:
        return []
    values: list[str] = []
    for part in forwarded_for.split(","):
        normalized = parse_ip_candidate(part)
        if normalized:
            values.append(normalized)
    return values


def is_public_ip(value: str | None) -> bool:
    parsed_value = parse_ip_candidate(value)
    if not parsed_value:
        return False
    parsed = ipaddress.ip_address(parsed_value)
    return not (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_reserved
        or parsed.is_unspecified
        or parsed.is_multicast
    )


def is_rfc1918_or_loopback(value: str | None) -> bool:
    parsed_value = parse_ip_candidate(value)
    if not parsed_value:
        return False
    ip = ipaddress.ip_address(parsed_value)
    if ip.version == 4:
        return (
            ip in ipaddress.ip_network("10.0.0.0/8")
            or ip in ipaddress.ip_network("172.16.0.0/12")
            or ip in ipaddress.ip_network("192.168.0.0/16")
            or ip in ipaddress.ip_network("127.0.0.0/8")
        )
    return ip.is_loopback
