import httpx
import pytest

from flow_agent.tools.web import (
    create_read_url_tool,
    validate_public_url,
)


PUBLIC_IP = "93.184.216.34"


def public_resolver(
    hostname: str,
    port: int,
) -> tuple[str, ...]:
    return (PUBLIC_IP,)


def make_client_factory(handler):
    def factory() -> httpx.Client:
        return httpx.Client(
            transport=httpx.MockTransport(
                handler
            ),
            follow_redirects=False,
            timeout=1.0,
        )

    return factory
  
def test_validate_public_url_accepts_public_address():
    validate_public_url(
        "https://example.com/page",
        resolver=public_resolver,
    )
    
@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/file.txt",
        "javascript:alert(1)",
    ],
)
def test_validate_public_url_rejects_unsupported_scheme(
    url,
):
    with pytest.raises(
        ValueError,
        match="scheme",
    ):
        validate_public_url(
            url,
            resolver=public_resolver,
        )
        
def test_validate_public_url_requires_hostname():
    with pytest.raises(
        ValueError,
        match="hostname",
    ):
        validate_public_url(
            "https:///page",
            resolver=public_resolver,
        )
        
def test_validate_public_url_rejects_credentials():
    with pytest.raises(
        ValueError,
        match="credentials",
    ):
        validate_public_url(
            "https://user:password@example.com/",
            resolver=public_resolver,
        )
  
def test_validate_public_url_rejects_invalid_port():
    with pytest.raises(
        ValueError,
        match="invalid port",
    ):
        validate_public_url(
            "https://example.com:not-a-port/",
            resolver=public_resolver,
        )
        
@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254",
        "::1",
        "fe80::1",
    ],
)
def test_validate_public_url_rejects_non_public_address(
    address,
):
    def resolver(
        hostname: str,
        port: int,
    ) -> tuple[str, ...]:
        return (address,)

    with pytest.raises(
        ValueError,
        match="non-public",
    ):
        validate_public_url(
            "https://example.com/",
            resolver=resolver,
        )
        
def test_validate_public_url_rejects_mixed_dns_results():
    def resolver(
        hostname: str,
        port: int,
    ) -> tuple[str, ...]:
        return (
            PUBLIC_IP,
            "127.0.0.1",
        )

    with pytest.raises(
        ValueError,
        match="non-public",
    ):
        validate_public_url(
            "https://example.com/",
            resolver=resolver,
        )
        
def test_validate_public_url_rejects_empty_dns_result():
    def resolver(
        hostname: str,
        port: int,
    ) -> tuple[str, ...]:
        return ()

    with pytest.raises(
        ValueError,
        match="could not be resolved",
    ):
        validate_public_url(
            "https://example.com/",
            resolver=resolver,
        )
        
def test_read_url_reads_text_response():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            headers={
                "content-type":
                    "text/plain; charset=utf-8",
            },
            content=b"hello FlowAgent",
        )

    read_url = create_read_url_tool(
        resolver=public_resolver,
        client_factory=make_client_factory(
            handler
        ),
    )

    result = read_url.invoke(
        {
            "url":
                "https://example.com/page",
        }
    )

    assert result == "hello FlowAgent"
    
def test_read_url_reads_json_response():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            headers={
                "content-type":
                    "application/json",
            },
            content=b'{"status":"ok"}',
        )

    read_url = create_read_url_tool(
        resolver=public_resolver,
        client_factory=make_client_factory(
            handler
        ),
    )

    result = read_url.invoke(
        {
            "url":
                "https://example.com/data",
        }
    )

    assert result == '{"status":"ok"}'
    
def test_read_url_rejects_binary_content():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            headers={
                "content-type": "image/png",
            },
            content=b"not really png",
        )

    read_url = create_read_url_tool(
        resolver=public_resolver,
        client_factory=make_client_factory(
            handler
        ),
    )

    with pytest.raises(
        ValueError,
        match="supported text content",
    ):
        read_url.invoke(
            {
                "url":
                    "https://example.com/image",
            }
        )
        
def test_read_url_propagates_http_error():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            404,
            headers={
                "content-type": "text/plain",
            },
            content=b"not found",
        )

    read_url = create_read_url_tool(
        resolver=public_resolver,
        client_factory=make_client_factory(
            handler
        ),
    )

    with pytest.raises(
        httpx.HTTPStatusError
    ):
        read_url.invoke(
            {
                "url":
                    "https://example.com/missing",
            }
        )
        
def test_read_url_rejects_large_response():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            headers={
                "content-type": "text/plain",
            },
            content=b"123456",
        )

    read_url = create_read_url_tool(
        resolver=public_resolver,
        client_factory=make_client_factory(
            handler
        ),
        max_response_bytes=5,
    )

    with pytest.raises(
        ValueError,
        match="too large",
    ):
        read_url.invoke(
            {
                "url":
                    "https://example.com/large",
            }
        )
        
def test_read_url_follows_safe_redirect():
    requested_urls = []

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        requested_urls.append(
            str(request.url)
        )

        if request.url.host == "example.com":
            return httpx.Response(
                302,
                headers={
                    "location":
                        "https://docs.example.com/final"
                },
            )

        return httpx.Response(
            200,
            headers={
                "content-type": "text/plain",
            },
            content=b"redirected",
        )

    read_url = create_read_url_tool(
        resolver=public_resolver,
        client_factory=make_client_factory(
            handler
        ),
    )

    result = read_url.invoke(
        {
            "url":
                "https://example.com/start",
        }
    )

    assert result == "redirected"

    assert requested_urls == [
        "https://example.com/start",
        "https://docs.example.com/final",
    ]
    
def test_read_url_rejects_redirect_to_private_address():
    requested_urls = []

    def resolver(
        hostname: str,
        port: int,
    ) -> tuple[str, ...]:
        if hostname == "example.com":
            return (PUBLIC_IP,)

        if hostname == "127.0.0.1":
            return ("127.0.0.1",)

        raise AssertionError(
            f"Unexpected hostname: {hostname}"
        )

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        requested_urls.append(
            str(request.url)
        )

        return httpx.Response(
            302,
            headers={
                "location":
                    "http://127.0.0.1/admin"
            },
        )

    read_url = create_read_url_tool(
        resolver=resolver,
        client_factory=make_client_factory(
            handler
        ),
    )

    with pytest.raises(
        ValueError,
        match="non-public",
    ):
        read_url.invoke(
            {
                "url":
                    "https://example.com/start",
            }
        )

    assert requested_urls == [
        "https://example.com/start",
    ]
    
def test_read_url_rejects_too_many_redirects():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            302,
            headers={
                "location":
                    "/next",
            },
        )

    read_url = create_read_url_tool(
        resolver=public_resolver,
        client_factory=make_client_factory(
            handler
        ),
        max_redirects=1,
    )

    with pytest.raises(
        ValueError,
        match="Too many redirects",
    ):
        read_url.invoke(
            {
                "url":
                    "https://example.com/start",
            }
        )
        
def test_read_url_rejects_redirect_without_location():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            302
        )

    read_url = create_read_url_tool(
        resolver=public_resolver,
        client_factory=make_client_factory(
            handler
        ),
    )

    with pytest.raises(
        ValueError,
        match="no location",
    ):
        read_url.invoke(
            {
                "url":
                    "https://example.com/start",
            }
        )
        
def test_read_url_propagates_timeout():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ReadTimeout(
            "read timed out",
            request=request,
        )

    read_url = create_read_url_tool(
        resolver=public_resolver,
        client_factory=make_client_factory(
            handler
        ),
    )

    with pytest.raises(
        httpx.ReadTimeout
    ):
        read_url.invoke(
            {
                "url":
                    "https://example.com/slow",
            }
        )