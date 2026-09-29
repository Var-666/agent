from ipaddress import ip_address
import socket
import httpx
from urllib.parse import urlsplit, urljoin

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

def create_read_url_tool() -> BaseTool:
  
  @tool("read_url")
  def read_url(url: str) -> str:
    """Read text content from a public HTTP or HTTPS URL."""
    
    current_url = url
    
    for redirect_count in range(DEFAULT_MAX_REDIRECTS + 1):
      validate_public_url(current_url)
      
      with httpx.stream("GET",current_url,timeout=DEFAULT_TIMEOUT_SECONDS,follow_redirects=False) as response:
        if (response.status_code in _REDIRECT_STATUS_CODES):
          if (redirect_count >= DEFAULT_MAX_REDIRECTS):
            raise ValueError("Too many redirects")
          
          location = response.headers.get("location")
          
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
        
        if not (content_type.startswith("text/") or content_type in _ALLOWED_APPLICATION_TYPES):
          raise ValueError("URL response is not supported text content")
        
        chunks: list[bytes] = []
        total_bytes = 0
        
        for chunk in response.iter_bytes():
          total_bytes += len(chunk)
          
          if (total_bytes > DEFAULT_MAX_RESPONSE_BYTES):
            raise ValueError("URL response is too large")
          
          chunks.append(chunk)
          
        body = b"".join(chunks)
        
        encoding = (response.encoding or "utf-8")
        
        return body.decode(encoding,errors="replace")
      
    raise ValueError("Too many redirects")
    
  return read_url
 
def validate_public_url(url: str) -> None:
  parsed = urlsplit(url)
  
  if parsed.scheme not in {"http","https"}:
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
    port = (443 if parsed.scheme == "https" else 80)
  
  addresses = socket.getaddrinfo(parsed.hostname,port,type=socket.SOCK_STREAM)
  
  if not addresses:
    raise ValueError("URL hostname could not be resolved")
  
  for address in addresses:
    host = address[4][0]
    resolved_ip = ip_address(host)
    
    if not resolved_ip.is_global:
      raise ValueError("URL resolves to a non-public address")