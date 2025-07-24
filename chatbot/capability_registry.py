"""
Capability Registry for MCP
Provides a clean interface for registering and managing capabilities
"""

import logging
from typing import Dict, List, Type
from .mcp_core import MCPCapability, MCPOrchestrator

logger = logging.getLogger(__name__)


class CapabilityRegistry:
    """Registry for managing MCP capabilities"""

    def __init__(self):
        self._capabilities: Dict[str, MCPCapability] = {}
        self._orchestrator: MCPOrchestrator = None

    def register(self, capability: MCPCapability) -> None:
        """Register a new capability"""
        if capability.name in self._capabilities:
            logger.warning(f"Capability '{capability.name}' is already registered. Overwriting.")

        self._capabilities[capability.name] = capability
        logger.info(f"Registered capability: {capability.name}")

    def unregister(self, name: str) -> bool:
        """Unregister a capability by name"""
        if name in self._capabilities:
            del self._capabilities[name]
            logger.info(f"Unregistered capability: {name}")
            return True
        return False

    def get(self, name: str) -> MCPCapability:
        """Get a capability by name"""
        return self._capabilities.get(name)

    def list_capabilities(self) -> List[str]:
        """List all registered capability names"""
        return list(self._capabilities.keys())

    def get_all_capabilities(self) -> List[MCPCapability]:
        """Get all registered capabilities"""
        return list(self._capabilities.values())

    def set_orchestrator(self, orchestrator: MCPOrchestrator) -> None:
        """Set the orchestrator instance"""
        self._orchestrator = orchestrator

    def sync_to_orchestrator(self) -> None:
        """Sync registered capabilities to the orchestrator"""
        if not self._orchestrator:
            logger.error("No orchestrator set. Cannot sync capabilities.")
            return

        # Clear existing capabilities
        self._orchestrator.capabilities.clear()

        # Register all capabilities
        for capability in self._capabilities.values():
            self._orchestrator.register_capability(capability)

        logger.info(f"Synced {len(self._capabilities)} capabilities to orchestrator")


# Global registry instance
capability_registry = CapabilityRegistry()


def register_capability(capability: MCPCapability) -> None:
    """Register a capability with the global registry"""
    capability_registry.register(capability)


def unregister_capability(name: str) -> bool:
    """Unregister a capability from the global registry"""
    return capability_registry.unregister(name)


def get_capability(name: str) -> MCPCapability:
    """Get a capability from the global registry"""
    return capability_registry.get(name)


def list_capabilities() -> List[str]:
    """List all registered capabilities"""
    return capability_registry.list_capabilities()


def sync_capabilities() -> None:
    """Sync all registered capabilities to the orchestrator"""
    capability_registry.sync_to_orchestrator()