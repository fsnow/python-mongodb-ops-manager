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
Users service for MongoDB Ops Manager API.

Provides read access to Ops Manager users by ID or username. Useful for
resolving user IDs found in event log entries to human-readable names
during audit reporting.

See: https://www.mongodb.com/docs/ops-manager/current/reference/api/users/
"""

from opsmanager.services.base import BaseService
from opsmanager.types import User


class UsersService(BaseService):
    """Service for reading Ops Manager users.

    Provides user lookup by ID and by username. Primarily useful for
    enriching audit reports — resolving ``userId`` fields in event logs
    to display names and email addresses.
    """

    def get(
        self,
        user_id: str,
        as_obj: bool = True,
    ) -> User:
        """Get a user by ID.

        Args:
            user_id: User ID.
            as_obj: Return User object if True, dict if False.

        Returns:
            User details.
        """
        response = self._get(f"users/{user_id}")
        return User.from_dict(response) if as_obj else response

    def get_by_name(
        self,
        username: str,
        as_obj: bool = True,
    ) -> User:
        """Get a user by username.

        Args:
            username: Username (typically an email address).
            as_obj: Return User object if True, dict if False.

        Returns:
            User details.
        """
        response = self._get(f"users/byName/{username}")
        return User.from_dict(response) if as_obj else response
