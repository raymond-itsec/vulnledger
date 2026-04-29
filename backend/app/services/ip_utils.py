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


def resolve_request_ip(request: Request, trust_proxy_headers: bool) -> str | None:
    direct_ip = parse_ip_candidate(request.client.host if request.client else None)
    if not trust_proxy_headers:
        return direct_ip

    x_real_ip = parse_ip_candidate(request.headers.get("x-real-ip"))
    forwarded_ips = extract_forwarded_ips(request)
    candidates = [x_real_ip, *forwarded_ips, direct_ip]
    for candidate in candidates:
        if is_public_ip(candidate):
            return candidate
    for candidate in candidates:
        if candidate:
            return candidate
    return None


def rate_limit_ip_key(request: Request, trust_proxy_headers: bool) -> str:
    return resolve_request_ip(request, trust_proxy_headers) or get_request_host_fallback(request)


def get_request_host_fallback(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
