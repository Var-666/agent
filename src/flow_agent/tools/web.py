from collections.abc import Callable
from ipaddress import ip_address
import socket
from urllib.parse import urljoin, urlsplit

import httpx
from langchain.tools import tool
from langchain_core.tools import BaseTool


DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RESPONSE_BYTES = 1_000_000
DEFAULT_MAX_REDIRECTS = 3

_REDIRECT_STATUS_CODES = {
    301,
    302,
    303,
    307,
    308,
}

_ALLOWED_APPLICATION_TYPES = {
    "application/json",
    "application/xml",
}


AddressResolver = Callable[
    [str, int],
    tuple[str, ...],
]

ClientFactory = Callable[
    [],
    httpx.Client,
]


def resolve_host_addresses(hostname: str, port: int,) -> tuple[str, ...]:
    addresses = socket.getaddrinfo(hostname,port,type=socket.SOCK_STREAM)

    return tuple(
        dict.fromkeys(address[4][0]
            for address in addresses
        )
    )


def validate_public_url(url: str, *,
    resolver: AddressResolver = (
        resolve_host_addresses
    ),
) -> str:
    parsed = urlsplit(url)

    if parsed.scheme not in {"http", "https",}:
        raise ValueError("URL scheme must be http or https")

    if not parsed.hostname:
        raise ValueError("URL must include a hostname")

    if parsed.username or parsed.password:
        raise ValueError("URL credentials are not allowed")

    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("URL contains an invalid port") from exc

    if port is None:
        port = (
            443
            if parsed.scheme == "https"
            else 80
        )

    addresses = resolver(parsed.hostname,port)

    if not addresses:
        raise ValueError("URL hostname could not be resolved")

    for host in addresses:
        resolved_ip = ip_address(host)

        if not resolved_ip.is_global:
            raise ValueError("URL resolves to a non-public address")

    return str(ip_address(addresses[0]))


def _create_default_client() -> httpx.Client:
    return httpx.Client(
        timeout=DEFAULT_TIMEOUT_SECONDS,
        follow_redirects=False,
        trust_env=False,
    )


def create_read_url_tool(
    *,
    resolver: AddressResolver = (resolve_host_addresses),
    client_factory: ClientFactory = (_create_default_client),
    max_response_bytes: int = (DEFAULT_MAX_RESPONSE_BYTES),
    max_redirects: int = (DEFAULT_MAX_REDIRECTS),
) -> BaseTool:

    @tool("read_url")
    def read_url(url: str) -> str:
        """Read text content from a public HTTP or HTTPS URL."""

        current_url = url.strip()

        with client_factory() as client:
            for redirect_count in range(max_redirects + 1):
                approved_ip = validate_public_url(current_url,resolver=resolver)
                parsed = urlsplit(current_url)
                pinned_url = httpx.URL(current_url).copy_with(host=approved_ip)

                with client.stream(
                    "GET",
                    pinned_url,
                    headers={"Host": parsed.netloc},
                    extensions={"sni_hostname": parsed.hostname},
                    follow_redirects=False,
                ) as response:

                    if (response.status_code in _REDIRECT_STATUS_CODES):
                        if (redirect_count>= max_redirects):
                            raise ValueError("Too many redirects")

                        location = (response.headers.get("location"))

                        if not location:
                            raise ValueError("Redirect response has no location")

                        current_url = urljoin(current_url,location)

                        continue

                    response.raise_for_status()

                    content_type = (
                        response.headers
                        .get("content-type", "")
                        .split(";", 1)[0]
                        .strip()
                        .lower()
                    )

                    if not (
                        content_type.startswith("text/")
                        or content_type in _ALLOWED_APPLICATION_TYPES
                    ):
                        raise ValueError("URL response is not supported text content")

                    chunks: list[bytes] = []
                    total_bytes = 0

                    for chunk in (response.iter_bytes()):
                        total_bytes += len(chunk)

                        if (total_bytes > max_response_bytes):
                            raise ValueError("URL response is too large")

                        chunks.append(chunk)

                    body = b"".join(chunks)

                    encoding = (response.encoding or "utf-8")

                    return body.decode(encoding,errors="replace")

        raise ValueError("Too many redirects")

    return read_url
