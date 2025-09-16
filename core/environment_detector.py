#!/usr/bin/env python3
"""
Environment detection and configuration system.

Detects the runtime environment (WSL, native Linux, macOS, Windows)
and applies appropriate configurations for optimal performance.
"""

import os
import sys
import platform
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentInfo:
    """Information about the detected environment."""
    os_type: str  # 'Linux', 'Darwin', 'Windows'
    is_wsl: bool
    is_docker: bool
    is_ssh: bool
    is_remote_desktop: bool
    display_server: Optional[str]  # 'x11', 'wayland', 'wslg', None
    gpu_available: bool
    gpu_vendor: Optional[str]  # 'nvidia', 'amd', 'intel', None


class EnvironmentDetector:
    """Detects the runtime environment and its capabilities."""
    
    @staticmethod
    def detect() -> EnvironmentInfo:
        """Detect the current environment."""
        os_type = platform.system()
        
        return EnvironmentInfo(
            os_type=os_type,
            is_wsl=EnvironmentDetector._is_wsl(),
            is_docker=EnvironmentDetector._is_docker(),
            is_ssh=EnvironmentDetector._is_ssh(),
            is_remote_desktop=EnvironmentDetector._is_remote_desktop(),
            display_server=EnvironmentDetector._detect_display_server(),
            gpu_available=EnvironmentDetector._check_gpu_available(),
            gpu_vendor=EnvironmentDetector._detect_gpu_vendor()
        )
    
    @staticmethod
    def _is_wsl() -> bool:
        """Check if running in WSL."""
        if platform.system() != 'Linux':
            return False
            
        # Check for WSL-specific indicators
        try:
            with open('/proc/version', 'r') as f:
                version = f.read().lower()
                return 'microsoft' in version or 'wsl' in version
        except (FileNotFoundError, PermissionError, IOError) as e:
            logger.debug(f"Cannot read /proc/version: {e}")
            pass
            
        # Check for WSL environment variable
        return 'WSL_DISTRO_NAME' in os.environ or 'WSL_INTEROP' in os.environ
    
    @staticmethod
    def _is_docker() -> bool:
        """Check if running in Docker container."""
        # Check for .dockerenv file
        if os.path.exists('/.dockerenv'):
            return True
            
        # Check cgroup for docker
        try:
            with open('/proc/1/cgroup', 'r') as f:
                return 'docker' in f.read()
        except (FileNotFoundError, PermissionError, IOError) as e:
            logger.debug(f"Cannot read /proc/1/cgroup: {e}")
            return False
    
    @staticmethod
    def _is_ssh() -> bool:
        """Check if running over SSH."""
        return 'SSH_CLIENT' in os.environ or 'SSH_TTY' in os.environ
    
    @staticmethod
    def _is_remote_desktop() -> bool:
        """Check if running in remote desktop session."""
        return 'REMOTE_DESKTOP_SESSION' in os.environ or 'RDP_SESSION' in os.environ
    
    @staticmethod
    def _detect_display_server() -> Optional[str]:
        """Detect the display server type."""
        if 'WAYLAND_DISPLAY' in os.environ:
            return 'wayland'
        elif 'DISPLAY' in os.environ:
            # Check if WSLg
            if os.environ.get('WSL_DISTRO_NAME'):
                return 'wslg'
            return 'x11'
        return None
    
    @staticmethod
    def _check_gpu_available() -> bool:
        """Check if GPU acceleration is available."""
        try:
            # Try to run glxinfo
            result = subprocess.run(['glxinfo'],
                                  capture_output=True,
                                  text=True,
                                  timeout=2)
            return 'direct rendering: Yes' in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
            logger.debug(f"Cannot run glxinfo to check GPU: {e}")
            return False
    
    @staticmethod
    def _detect_gpu_vendor() -> Optional[str]:
        """Detect GPU vendor."""
        try:
            result = subprocess.run(['glxinfo'],
                                  capture_output=True,
                                  text=True,
                                  timeout=2)
            output = result.stdout.lower()

            if 'nvidia' in output:
                return 'nvidia'
            elif 'amd' in output or 'radeon' in output:
                return 'amd'
            elif 'intel' in output:
                return 'intel'
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
            logger.debug(f"Cannot run glxinfo to detect GPU vendor: {e}")
            pass
        
        return None


class EnvironmentStrategy(ABC):
    """Abstract base class for environment configuration strategies."""
    
    @abstractmethod
    def configure(self) -> Dict[str, str]:
        """
        Configure environment variables for the platform.
        
        Returns:
            Dictionary of environment variables to set
        """
        pass
    
    @abstractmethod
    def get_qt_flags(self) -> Dict[str, str]:
        """
        Get Qt-specific configuration flags.
        
        Returns:
            Dictionary of Qt environment variables
        """
        pass
    
    @abstractmethod
    def get_recommendations(self) -> str:
        """
        Get human-readable recommendations for this environment.
        
        Returns:
            String with recommendations
        """
        pass


class WSLStrategy(EnvironmentStrategy):
    """Configuration strategy for WSL environment."""
    
    def configure(self) -> Dict[str, str]:
        """Configure for WSL environment."""
        env_vars = {
            # Core settings for WSL compatibility
            'LIBGL_ALWAYS_SOFTWARE': '1',  # Force software rendering
            'QTWEBENGINE_DISABLE_SANDBOX': '1',  # Sandbox doesn't work well in WSL
            'QTWEBENGINE_CHROMIUM_FLAGS': '--disable-gpu --no-sandbox --disable-dev-shm-usage',
            
            # Let Qt choose the best backend, but use software
            'QT_QUICK_BACKEND': 'software',
        }
        
        # Don't force a specific platform - let Qt auto-detect
        # WSLg can use either Wayland or X11 depending on setup
        
        if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
            logger.warning("No DISPLAY or WAYLAND_DISPLAY set - application may not show")
            
        return env_vars
    
    def get_qt_flags(self) -> Dict[str, str]:
        """Get Qt flags for WSL."""
        return {
            'QT_SCALE_FACTOR': '1',
            'QT_AUTO_SCREEN_SCALE_FACTOR': '0',
            'QT_ENABLE_HIGHDPI_SCALING': '1'
        }
    
    def get_recommendations(self) -> str:
        """Get WSL recommendations."""
        return """
WSL Environment Detected:
- Using software rendering for stability
- Terminal features may be limited
- Consider using WSLg for better graphics support
- For best performance, use native Linux
"""


class NativeLinuxStrategy(EnvironmentStrategy):
    """Configuration strategy for native Linux."""
    
    def __init__(self, env_info: EnvironmentInfo):
        self.env_info = env_info
    
    def configure(self) -> Dict[str, str]:
        """Configure for native Linux."""
        env_vars = {}
        
        # Only disable GPU if it's not available
        if not self.env_info.gpu_available:
            env_vars['QT_QUICK_BACKEND'] = 'software'
            env_vars['LIBGL_ALWAYS_SOFTWARE'] = '1'
            
        # Wayland-specific settings
        if self.env_info.display_server == 'wayland':
            env_vars['QT_QPA_PLATFORM'] = 'wayland'
            
        return env_vars
    
    def get_qt_flags(self) -> Dict[str, str]:
        """Get Qt flags for native Linux."""
        return {
            'QT_AUTO_SCREEN_SCALE_FACTOR': '1'
        }
    
    def get_recommendations(self) -> str:
        """Get native Linux recommendations."""
        gpu_status = "available" if self.env_info.gpu_available else "not detected"
        return f"""
Native Linux Environment:
- GPU acceleration: {gpu_status}
- Display server: {self.env_info.display_server or 'unknown'}
- Full terminal features available
"""


class MacOSStrategy(EnvironmentStrategy):
    """Configuration strategy for macOS."""
    
    def configure(self) -> Dict[str, str]:
        """Configure for macOS."""
        return {
            'QT_MAC_WANTS_LAYER': '1'
        }
    
    def get_qt_flags(self) -> Dict[str, str]:
        """Get Qt flags for macOS."""
        return {
            'QT_AUTO_SCREEN_SCALE_FACTOR': '1'
        }
    
    def get_recommendations(self) -> str:
        """Get macOS recommendations."""
        return """
macOS Environment:
- Metal rendering enabled
- Full terminal features available
"""


class WindowsStrategy(EnvironmentStrategy):
    """Configuration strategy for Windows."""
    
    def configure(self) -> Dict[str, str]:
        """Configure for Windows."""
        return {
            'QT_OPENGL': 'angle'  # Use ANGLE for better compatibility
        }
    
    def get_qt_flags(self) -> Dict[str, str]:
        """Get Qt flags for Windows."""
        return {
            'QT_AUTO_SCREEN_SCALE_FACTOR': '1',
            'QT_ENABLE_HIGHDPI_SCALING': '1'
        }
    
    def get_recommendations(self) -> str:
        """Get Windows recommendations."""
        return """
Windows Environment:
- Using ANGLE for OpenGL compatibility
- Terminal features may be limited
- Consider using WSL2 for better Unix compatibility
"""


class DockerStrategy(EnvironmentStrategy):
    """Configuration strategy for Docker containers."""
    
    def configure(self) -> Dict[str, str]:
        """Configure for Docker."""
        return {
            'QT_QUICK_BACKEND': 'software',
            'QT_XCB_GL_INTEGRATION': 'none',
            'LIBGL_ALWAYS_SOFTWARE': '1',
            'QTWEBENGINE_DISABLE_SANDBOX': '1'
        }
    
    def get_qt_flags(self) -> Dict[str, str]:
        """Get Qt flags for Docker."""
        return {
            'QT_X11_NO_MITSHM': '1'  # Disable shared memory for X11
        }
    
    def get_recommendations(self) -> str:
        """Get Docker recommendations."""
        return """
Docker Environment:
- Using software rendering
- Ensure X11 socket is mounted
- Terminal features may be limited
"""


class SSHStrategy(EnvironmentStrategy):
    """Configuration strategy for SSH sessions."""
    
    def configure(self) -> Dict[str, str]:
        """Configure for SSH."""
        return {
            'QT_QUICK_BACKEND': 'software',
            'LIBGL_ALWAYS_SOFTWARE': '1'
        }
    
    def get_qt_flags(self) -> Dict[str, str]:
        """Get Qt flags for SSH."""
        return {
            'QT_X11_NO_MITSHM': '1'
        }
    
    def get_recommendations(self) -> str:
        """Get SSH recommendations."""
        return """
SSH Session Detected:
- Using software rendering for stability
- Ensure X11 forwarding is enabled (ssh -X)
- Performance may be limited over network
"""


class EnvironmentConfigurator:
    """Main configurator that applies the appropriate strategy."""
    
    def __init__(self):
        self.env_info = EnvironmentDetector.detect()
        self.strategy = self._select_strategy()
        
    def _select_strategy(self) -> EnvironmentStrategy:
        """Select the appropriate strategy based on environment."""
        # Priority order matters - check most specific first
        
        if self.env_info.is_docker:
            logger.info("Docker environment detected")
            return DockerStrategy()
            
        if self.env_info.is_ssh:
            logger.info("SSH session detected")
            return SSHStrategy()
            
        if self.env_info.is_wsl:
            logger.info("WSL environment detected")
            return WSLStrategy()
            
        if self.env_info.os_type == 'Linux':
            logger.info("Native Linux environment detected")
            return NativeLinuxStrategy(self.env_info)
            
        if self.env_info.os_type == 'Darwin':
            logger.info("macOS environment detected")
            return MacOSStrategy()
            
        if self.env_info.os_type == 'Windows':
            logger.info("Windows environment detected")
            return WindowsStrategy()
            
        # Fallback to software rendering
        logger.warning("Unknown environment, using safe defaults")
        return WSLStrategy()  # Safe defaults
    
    def apply_configuration(self) -> None:
        """Apply the environment configuration."""
        # Get configuration from strategy
        env_vars = self.strategy.configure()
        qt_flags = self.strategy.get_qt_flags()
        
        # Merge configurations
        all_vars = {**env_vars, **qt_flags}
        
        # Apply environment variables
        for key, value in all_vars.items():
            os.environ[key] = value
            logger.debug(f"Set {key}={value}")
            
        # Log recommendations
        logger.info(self.strategy.get_recommendations())
    
    def get_info(self) -> Tuple[EnvironmentInfo, EnvironmentStrategy]:
        """Get environment info and selected strategy."""
        return self.env_info, self.strategy