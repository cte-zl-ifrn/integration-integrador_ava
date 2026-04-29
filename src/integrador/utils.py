import logging
import sc4net
import json
from http.client import HTTPException
from typing import NoReturn
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 10


class SyncError(Exception):
    def __init__(self, message, code, retorno=None, params=None):
        super().__init__(message, code, params)
        self.message = message
        self.code = code
        self.retorno = retorno
        logger.debug(f"{code}: {message} - {retorno}")


def validate_http_response(url, encoding, decode, response):
    if response.ok:
        byte_array_content = response.content
        return byte_array_content.decode(encoding) if decode and encoding is not None else byte_array_content
    else:
        exc = HTTPException("%s - %s - %s" % (response.status_code, response.reason, response.content))
        exc.status = response.status_code
        exc.reason = response.reason
        exc.headers = response.headers or {}
        exc.url = url
        raise exc


def http_get(url, headers: dict | None = None, encoding="utf-8", decode=True, **kwargs):
    timeout = kwargs.pop("timeout", REQUEST_TIMEOUT_SECONDS)
    return sc4net.get(url, headers=headers or {}, encoding=encoding, decode=decode, timeout=timeout, **kwargs)


def http_post(url, jsonbody: dict | None = None, headers: dict | None = None, encoding="utf-8", decode=True, **kwargs):
    def _raise_http_exception(status, reason, url, headers=None) -> NoReturn:
        exc = HTTPException("%s - %s" % (status, reason))
        setattr(exc, "status", status)
        setattr(exc, "reason", reason)
        setattr(exc, "headers", headers or {})
        setattr(exc, "url", url)
        raise exc

    def _merge_headers(headers):
        result = {}
        if headers:
            result.update(headers)
        return result

    def _validate_web_url(url):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            _raise_http_exception(400, "Only http/https URLs are allowed", url)

    def _build_post_payload(data, json_data, request_headers, encoding):
        if json_data is not None:
            payload = json.dumps(json_data).encode(encoding or "utf-8")
            if "Content-Type" not in request_headers:
                request_headers["Content-Type"] = "application/json"
            return payload

        if data is None:
            return None

        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode(encoding or "utf-8")
        if isinstance(data, dict):
            payload = urlencode(data, doseq=True).encode(encoding or "utf-8")
            if "Content-Type" not in request_headers:
                request_headers["Content-Type"] = "application/x-www-form-urlencoded"
            return payload

        return str(data).encode(encoding or "utf-8")

    _validate_web_url(url)
    timeout = kwargs.pop("timeout", REQUEST_TIMEOUT_SECONDS)
    timeout = kwargs.get("timeout")
    request_headers = _merge_headers(headers)
    payload = _build_post_payload(None, jsonbody, request_headers, encoding)
    request = Request(url, data=payload, headers=request_headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310
            byte_array_content = response.read()
    except HTTPError as exc:
        print(f"HTTPError: {exc.code} - {exc.reason} - {exc.read()}")
        _raise_http_exception(exc.code, exc.reason, url, dict(exc.headers or {}))
    except URLError as exc:
        print(f"URLError: {exc.code} - {exc.reason} - {exc.read()}")
        _raise_http_exception(502, str(exc.reason), url)

    result = byte_array_content.decode(encoding) if decode and encoding is not None else byte_array_content

    # result = sc4net.post(
    #     url,
    #     json_data=jsonbody or {},
    #     headers=headers or {},
    #     encoding=encoding,
    #     decode=decode,
    #     timeout=timeout,
    #     **kwargs,
    # )
    print("HTTP POST Result:", result)
    return result


def http_get_json(url, headers={}, encoding="utf-8", json_kwargs=None, **kwargs):
    content = http_get(url, headers=headers, encoding=encoding, **kwargs)
    return json.loads(content, **(json_kwargs or {}))


def http_post_json(
    url, jsonbody: dict | None = None, headers: dict | None = None, encoding="utf-8", json_kwargs=None, **kwargs
):
    content = http_post(url, jsonbody=jsonbody, headers=headers or {}, encoding=encoding, **kwargs)
    result = json.loads(content, **(json_kwargs or {}))
    print(result)
    return result
