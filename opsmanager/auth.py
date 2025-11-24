# Copyright 2024 Frank Snow
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Authentication module for MongoDB Ops Manager API.

The Ops Manager API uses HTTP Digest Authentication with API key pairs.
This module provides the authentication handler for requests.
"""

from requests.auth import HTTPDigestAuth
from typing import Optional


class OpsManagerAuth(HTTPDigestAuth):
    """HTTP Digest Authentication for Ops Manager API.

    Ops Manager uses HTTP Digest Authentication with a public/private API key pair.
    The public key is used as the username and the private key as the password.

    Example:
        auth = OpsManagerAuth(
            public_key="your-public-key",
            private_key="your-private-key"
        )

        # Used with requests
        response = requests.get(url, auth=auth)

    Note:
        API keys can be created at either the Organization or Project level
        in Ops Manager. The key's permissions determine which API endpoints
        are accessible.
    """

    def __init__(self, public_key: str, private_key: str):
        """Initialize the authentication handler.

        Args:
            public_key: The Ops Manager API public key (used as username).
            private_key: The Ops Manager API private key (used as password).
        """
        super().__init__(username=public_key, password=private_key)
        self._public_key = public_key

    @property
    def public_key(self) -> str:
        """Return the public key (for logging/debugging, not the private key)."""
        return self._public_key

    def __repr__(self) -> str:
        # Mask the private key in repr for security
        return f"OpsManagerAuth(public_key={self._public_key!r}, private_key='***')"


def create_auth(
    public_key: Optional[str] = None,
    private_key: Optional[str] = None,
) -> OpsManagerAuth:
    """Create an authentication handler from API keys.

    Args:
        public_key: The Ops Manager API public key.
        private_key: The Ops Manager API private key.

    Returns:
        OpsManagerAuth: Configured authentication handler.

    Raises:
        ValueError: If public_key or private_key is not provided.

    Note:
        In a future version, this could support loading keys from
        environment variables or configuration files.
    """
    if not public_key:
        raise ValueError("public_key is required")
    if not private_key:
        raise ValueError("private_key is required")

    return OpsManagerAuth(public_key=public_key, private_key=private_key)
