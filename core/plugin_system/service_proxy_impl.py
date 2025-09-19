"""Service proxy implementation for plugins."""

from typing import Dict, Any
from viloapp_sdk import ServiceProxy
from .service_adapters import create_service_adapters

class ServiceProxyImpl(ServiceProxy):
    """Implementation of service proxy for ViloxTerm."""

    def __init__(self, services: Dict[str, Any]):
        # Create service adapters that expose SDK interfaces
        adapters = create_service_adapters(services)

        # Combine original services with adapters
        all_services = {**services, **adapters}

        super().__init__(all_services)