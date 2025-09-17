from devpi_api_client.api.base import DevApiBase, logger


class Auth(DevApiBase):
    """
    Sub-client for login. Accessed via ``client.login``.
    """
    def user(self, username: str, password: str):
        """
        Authenticate via username/password

        :param username: Username
        :type username: str
        :param password: Password
        :type password: str
        """
        self._basic_auth(username, password)
        logger.debug(f"User ({username}) auth successful")

    def token(self, token: str):
        """
        Authenticate via token
        :param token: Token
        :type token: str
        """
        self._client.session.auth = ("__token__", token)
        logger.debug(f"Token auth successful")

    def _basic_auth(self, username: str, password: str):
        self._client.session.auth = (username, password)
