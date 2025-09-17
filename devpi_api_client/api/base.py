from urllib.parse import urljoin
import requests
from abc import ABCMeta
import logging

logger = logging.getLogger("DevpiApi")

class DevApiBase(metaclass=ABCMeta):
    """
    Sub-client for managing indexes. Accessed via ``client.index``.

    :param client: An instance of DevpiClient to provide request capabilities.
    :type client: DevpiClient
    """
    def __init__(self, client: 'Client') -> None:
        self._client = client

    def _request(self, method, path, return_json: bool = True, **kwargs):
        url = urljoin(self._client.base_url, path)
        try:
            r = self._client.session.request(url=url, method=method, **kwargs)
            r.raise_for_status()
            logger.debug(f"({method}) to {path} succeeded")
            return r.json() if return_json else r
        except requests.exceptions.RequestException as e:
            logger.error(f"({method}) to {path} failed: {r.text}")
            raise e