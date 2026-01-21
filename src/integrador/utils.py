import logging
import requests
import json
from http.client import HTTPException


logger = logging.getLogger(__name__)


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
    response: requests.Response = requests.get(url, headers=headers or {}, **kwargs)
    return validate_http_response(url, encoding, decode, response)



def http_post(url, jsonbody: dict | None = None, headers: dict | None = None, encoding="utf-8", decode=True, **kwargs):
    response: requests.Response = requests.post(url=url, json=jsonbody or {}, headers=headers or {}, **kwargs)
    return validate_http_response(url, encoding, decode, response)


def http_get_json(url, headers={}, encoding="utf-8", json_kwargs=None, **kwargs):
    content = http_get(url, headers=headers, encoding=encoding, **kwargs)
    return json.loads(content, **(json_kwargs or {}))


def http_post_json(url, jsonbody: dict | None = None, headers: dict | None = None, encoding="utf-8", json_kwargs=None, **kwargs):
    content = http_post(url, jsonbody=jsonbody, headers=headers or {}, encoding=encoding, **kwargs)
    return json.loads(content, **(json_kwargs or {}))
