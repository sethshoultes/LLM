#!/usr/bin/env python3
"""
API versioning module for the LLM Platform.

Provides functionality for API versioning, routing requests to the appropriate
version handlers, and managing API deprecation.
"""

import re
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

# Import core modules
try:
    from core.logging import get_logger
except ImportError:
    # Fallback if core module is not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    get_logger = lambda name: logging.getLogger(name)

# Import web modules
from web.router import Router

# Get logger for this module
logger = get_logger("web.api.versioning")


class ApiVersion(Enum):
    """Supported API versions."""
    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"


class ApiVersionManager:
    """
    API version manager.
    
    Handles routing requests to the appropriate version handlers and manages
    API deprecation and backwards compatibility.
    """
    
    def __init__(self):
        """Initialize API version manager."""
        # Map of API versions to route register functions
        self.version_routes = {}
        
        # Map of API versions to deprecation info
        self.deprecation_info = {}
        
        # Current latest version
        self.latest_version = ApiVersion.V1
    
    def register_version(self, version: ApiVersion, 
                      register_func: Callable[[Router, str], Router],
                      is_deprecated: bool = False,
                      deprecation_date: str = None,
                      end_of_life_date: str = None) -> None:
        """
        Register an API version.
        
        Args:
            version: API version to register
            register_func: Function to register routes for this version
            is_deprecated: Whether this version is deprecated
            deprecation_date: Date when this version was deprecated
            end_of_life_date: Date when this version will be removed
        """
        self.version_routes[version] = register_func
        
        # Set deprecation info if applicable
        if is_deprecated:
            self.deprecation_info[version] = {
                "is_deprecated": True,
                "deprecation_date": deprecation_date,
                "end_of_life_date": end_of_life_date
            }
        
        # Update latest version if needed
        if version != ApiVersion.LATEST and not is_deprecated:
            if version.value > self.latest_version.value:
                self.latest_version = version
    
    def set_latest_version(self, version: ApiVersion) -> None:
        """
        Set the latest API version.
        
        Args:
            version: Version to set as latest
        """
        if version not in self.version_routes:
            raise ValueError(f"Cannot set latest version to {version}, it is not registered")
        
        if version == ApiVersion.LATEST:
            raise ValueError("Cannot set LATEST as the latest version")
        
        self.latest_version = version
    
    def register_routes(self, router: Router) -> Router:
        """
        Register all API version routes with the router.
        
        Args:
            router: Router to register routes with
            
        Returns:
            Router with versioned routes registered
        """
        for version, register_func in self.version_routes.items():
            if version == ApiVersion.LATEST:
                continue
                
            # Create version route group
            version_group = router.group(f"/{version.value}")
            
            # Register routes for this version
            register_func(version_group, "")
            
            # Add deprecation header middleware if applicable
            if version in self.deprecation_info:
                self._add_deprecation_middleware(version_group, version)
            
            # Merge routes back to main router
            version_group.merge()
        
        # Register latest version routes
        if self.latest_version:
            # Create latest version route group
            latest_group = router.group("/latest")
            
            # Register routes using the latest version's register function
            self.version_routes[self.latest_version](latest_group, "")
            
            # Add latest version info middleware
            self._add_latest_middleware(latest_group)
            
            # Merge routes back to main router
            latest_group.merge()
        
        return router
    
    def _add_deprecation_middleware(self, router, version: ApiVersion) -> None:
        """
        Add deprecation header middleware to a router.
        
        Args:
            router: Router to add middleware to
            version: API version that is deprecated
        """
        deprecation_info = self.deprecation_info[version]
        
        def deprecation_middleware(request, response):
            """Add deprecation headers to the response."""
            response.set_header("API-Deprecated", "true")
            
            if deprecation_info.get("deprecation_date"):
                response.set_header("API-Deprecation-Date", deprecation_info["deprecation_date"])
                
            if deprecation_info.get("end_of_life_date"):
                response.set_header("API-End-Of-Life-Date", deprecation_info["end_of_life_date"])
                
            response.set_header("API-Latest-Version", self.latest_version.value)
            response.set_header("API-Version", version.value)
        
        # Add middleware to router
        if not hasattr(router, "middleware"):
            router.middleware = []
        
        router.middleware.append(deprecation_middleware)
    
    def _add_latest_middleware(self, router) -> None:
        """
        Add latest version info middleware to a router.
        
        Args:
            router: Router to add middleware to
        """
        def latest_middleware(request, response):
            """Add latest version headers to the response."""
            response.set_header("API-Latest-Version", self.latest_version.value)
            response.set_header("API-Version", self.latest_version.value)
        
        # Add middleware to router
        if not hasattr(router, "middleware"):
            router.middleware = []
        
        router.middleware.append(latest_middleware)


class VersionedRouter:
    """
    Versioned router for the API.
    
    Provides a router that routes requests to the appropriate API version.
    """
    
    def __init__(self, base_router: Router, version_manager: ApiVersionManager):
        """
        Initialize versioned router.
        
        Args:
            base_router: Base router to use for routing
            version_manager: API version manager
        """
        self.base_router = base_router
        self.version_manager = version_manager
        
        # Register versioned routes
        self.version_manager.register_routes(self.base_router)
    
    def get_router(self) -> Router:
        """
        Get the router with versioned routes.
        
        Returns:
            Router with versioned routes
        """
        return self.base_router


# Create singleton instance
version_manager = ApiVersionManager()


def create_versioned_router(base_router: Router) -> Router:
    """
    Create a versioned router.
    
    Args:
        base_router: Base router to use for routing
        
    Returns:
        Router with versioned routes
    """
    versioned_router = VersionedRouter(base_router, version_manager)
    return versioned_router.get_router()


def register_version_routes(router, version_string, register_func, 
                         is_deprecated=False, deprecation_date=None, 
                         end_of_life_date=None):
    """
    Register routes for an API version.
    
    Args:
        router: Router to register routes with
        version_string: Version string (e.g. "v1", "v2")
        register_func: Function to register routes for this version
        is_deprecated: Whether this version is deprecated
        deprecation_date: Date when this version was deprecated
        end_of_life_date: Date when this version will be removed
        
    Returns:
        Router with versioned routes registered
    """
    # Parse version string
    try:
        if version_string.lower() == "latest":
            version = ApiVersion.LATEST
        else:
            # Extract version number from string (e.g. "v1" -> "V1")
            match = re.match(r'v(\d+)', version_string.lower())
            if not match:
                raise ValueError(f"Invalid version string: {version_string}")
            
            version_name = f"V{match.group(1)}"
            version = getattr(ApiVersion, version_name)
    except (AttributeError, ValueError):
        raise ValueError(f"Unsupported API version: {version_string}")
    
    # Register version
    version_manager.register_version(
        version=version,
        register_func=register_func,
        is_deprecated=is_deprecated,
        deprecation_date=deprecation_date,
        end_of_life_date=end_of_life_date
    )
    
    return router