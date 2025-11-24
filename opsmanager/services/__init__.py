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
Service modules for MongoDB Ops Manager API.

Each service module corresponds to a section of the Ops Manager API.
"""

from opsmanager.services.base import BaseService
from opsmanager.services.organizations import OrganizationsService
from opsmanager.services.projects import ProjectsService
from opsmanager.services.clusters import ClustersService
from opsmanager.services.deployments import DeploymentsService
from opsmanager.services.measurements import MeasurementsService
from opsmanager.services.performance_advisor import PerformanceAdvisorService
from opsmanager.services.alerts import AlertsService

__all__ = [
    "BaseService",
    "OrganizationsService",
    "ProjectsService",
    "ClustersService",
    "DeploymentsService",
    "MeasurementsService",
    "PerformanceAdvisorService",
    "AlertsService",
]
