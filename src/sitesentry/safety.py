"""URL validation helpers: only public HTTP(S) hosts are scanned."""
import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeTarget(ValueError):
    pass


def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeTarget("Use a complete public http:// or https:// URL.")
    if parsed.username or parsed.password:
        raise UnsafeTarget("URLs containing usernames or passwords are not accepted.")
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise UnsafeTarget("Local and private network targets are not scanned.")
    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            addresses = {ipaddress.ip_address(result[4][0]) for result in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
        except OSError as exc:
            raise UnsafeTarget(f"Could not resolve {host}: {exc}") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise UnsafeTarget("Local, private, and reserved IP addresses are not scanned.")
    return url
