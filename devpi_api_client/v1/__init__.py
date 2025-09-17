import requests
from typing import Optional, Dict, Any, Union
from devpi_api_client.api import Token, Index, Project, Auth
import logging


logger = logging.getLogger("DevpiapiClient")


class Client:
    """
    Main client class that provides access to namespaced sub-clients
    for tokens, packages, and indexes
    """
    def __init__(self, base_url: str, user: Optional[str] = None, password: Optional[str] = None, token: Optional[str] = None, verify: Optional[Union[bool, str]] = True) -> None:
        """
        Initializes the unified client and handles authentication.

        :param base_url: The base URL of the devpi server (e.g., http://localhost:3141).
        :type base_url: str
        :param user: The username for password-based login.
        :type user: Optional[str]
        :param password: The password for password-based login.
        :type password: Optional[str]
        :param token: An authentication token. Takes precedence over user/password.
        :type token: Optional[str]
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers = {
            "Accept": "application/json"
        }
        self.session.verify = verify
        self.token = Token(self)
        self.package = Project(self)
        self.index = Index(self)
        self.auth = Auth(self)
        if token:
            self.auth.token(token)
        else:
            self.auth.user(user, password)
