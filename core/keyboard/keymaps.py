#!/usr/bin/env python3
"""
Keymap system for keyboard shortcuts.

This module provides different keymap configurations (default, vscode, vim)
and manages switching between them.
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import logging

from core.keyboard.shortcuts import Shortcut, ShortcutRegistry

logger = logging.getLogger(__name__)


@dataclass
class KeymapInfo:
    """Information about a keymap."""
    id: str
    name: str
    description: str
    version: str = "1.0"
    author: str = "ViloApp"
    shortcuts: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.shortcuts is None:
            self.shortcuts = []


class KeymapProvider(ABC):
    """Abstract base class for keymap providers."""
    
    @abstractmethod
    def get_info(self) -> KeymapInfo:
        """Get keymap information."""
        pass
    
    @abstractmethod
    def get_shortcuts(self) -> List[Dict[str, Any]]:
        """Get shortcuts for this keymap."""
        pass


class DefaultKeymapProvider(KeymapProvider):
    """Default keymap provider for ViloApp."""
    
    def get_info(self) -> KeymapInfo:
        """Get default keymap info."""
        return KeymapInfo(
            id="default",
            name="ViloApp Default",
            description="Default keyboard shortcuts for ViloApp",
            version="1.0"
        )
    
    def get_shortcuts(self) -> List[Dict[str, Any]]:
        """Get default shortcuts."""
        return [
            # File operations
            {"id": "file.new", "sequence": "ctrl+n", "command_id": "file.newEditorTab"},
            {"id": "file.open", "sequence": "ctrl+o", "command_id": "file.open"},
            {"id": "file.save", "sequence": "ctrl+s", "command_id": "file.save"},
            {"id": "file.save_as", "sequence": "ctrl+shift+s", "command_id": "file.saveAs"},
            {"id": "file.close", "sequence": "ctrl+w", "command_id": "file.closeActiveTab"},
            
            # Edit operations
            {"id": "edit.cut", "sequence": "ctrl+x", "command_id": "editor.cut"},
            {"id": "edit.copy", "sequence": "ctrl+c", "command_id": "editor.copy"},
            {"id": "edit.paste", "sequence": "ctrl+v", "command_id": "editor.paste"},
            {"id": "edit.undo", "sequence": "ctrl+z", "command_id": "editor.undo"},
            {"id": "edit.redo", "sequence": "ctrl+y", "command_id": "editor.redo"},
            {"id": "edit.select_all", "sequence": "ctrl+a", "command_id": "editor.selectAll"},
            
            # View operations
            {"id": "view.sidebar", "sequence": "ctrl+b", "command_id": "view.toggleSidebar"},
            {"id": "view.terminal", "sequence": "ctrl+`", "command_id": "view.toggleTerminal"},
            {"id": "view.fullscreen", "sequence": "f11", "command_id": "view.toggleFullscreen"},
            {"id": "view.theme", "sequence": "ctrl+t", "command_id": "view.toggleTheme"},
            
            # Workspace operations
            {"id": "workspace.split_horizontal", "sequence": "ctrl+shift+\\", "command_id": "workspace.splitActivePane", "args": {"orientation": "horizontal"}},
            {"id": "workspace.split_vertical", "sequence": "ctrl+\\", "command_id": "workspace.splitActivePane", "args": {"orientation": "vertical"}},
            {"id": "workspace.next_pane", "sequence": "ctrl+k ctrl+right", "command_id": "workspace.navigateToNextPane"},
            {"id": "workspace.prev_pane", "sequence": "ctrl+k ctrl+left", "command_id": "workspace.navigateToPreviousPane"},
            
            # Terminal operations
            {"id": "terminal.new", "sequence": "ctrl+shift+`", "command_id": "terminal.newTerminal"},
            {"id": "terminal.kill", "sequence": "ctrl+shift+k", "command_id": "terminal.killActiveTerminal"},
            
            # Help
            {"id": "help.about", "sequence": "f1", "command_id": "help.about"},
        ]


class VSCodeKeymapProvider(KeymapProvider):
    """VSCode-style keymap provider."""
    
    def get_info(self) -> KeymapInfo:
        """Get VSCode keymap info."""
        return KeymapInfo(
            id="vscode",
            name="VSCode",
            description="VSCode-style keyboard shortcuts",
            version="1.0"
        )
    
    def get_shortcuts(self) -> List[Dict[str, Any]]:
        """Get VSCode shortcuts."""
        return [
            # File operations
            {"id": "file.new", "sequence": "ctrl+n", "command_id": "file.newEditorTab"},
            {"id": "file.open", "sequence": "ctrl+o", "command_id": "file.open"},
            {"id": "file.save", "sequence": "ctrl+s", "command_id": "file.save"},
            {"id": "file.save_as", "sequence": "ctrl+shift+s", "command_id": "file.saveAs"},
            {"id": "file.close", "sequence": "ctrl+w", "command_id": "file.closeActiveTab"},
            {"id": "file.close_all", "sequence": "ctrl+k ctrl+w", "command_id": "file.closeAllTabs"},
            {"id": "file.reopen", "sequence": "ctrl+shift+t", "command_id": "file.reopenClosedTab"},
            
            # Edit operations
            {"id": "edit.cut", "sequence": "ctrl+x", "command_id": "editor.cut"},
            {"id": "edit.copy", "sequence": "ctrl+c", "command_id": "editor.copy"},
            {"id": "edit.paste", "sequence": "ctrl+v", "command_id": "editor.paste"},
            {"id": "edit.undo", "sequence": "ctrl+z", "command_id": "editor.undo"},
            {"id": "edit.redo", "sequence": "ctrl+shift+z", "command_id": "editor.redo"},
            {"id": "edit.select_all", "sequence": "ctrl+a", "command_id": "editor.selectAll"},
            
            # View operations
            {"id": "view.sidebar", "sequence": "ctrl+b", "command_id": "view.toggleSidebar"},
            {"id": "view.terminal", "sequence": "ctrl+`", "command_id": "view.toggleTerminal"},
            {"id": "view.fullscreen", "sequence": "f11", "command_id": "view.toggleFullscreen"},
            {"id": "view.command_palette", "sequence": "ctrl+shift+p", "command_id": "view.showCommandPalette"},
            
            # Workspace operations
            {"id": "workspace.split_editor", "sequence": "ctrl+\\", "command_id": "workspace.splitActivePane"},
            {"id": "workspace.focus_left", "sequence": "ctrl+k ctrl+left", "command_id": "workspace.navigateToPreviousPane"},
            {"id": "workspace.focus_right", "sequence": "ctrl+k ctrl+right", "command_id": "workspace.navigateToNextPane"},
            {"id": "workspace.close_group", "sequence": "ctrl+k w", "command_id": "workspace.closeActivePane"},
            
            # Navigation
            {"id": "nav.next_tab", "sequence": "ctrl+tab", "command_id": "workspace.switchToNextTab"},
            {"id": "nav.prev_tab", "sequence": "ctrl+shift+tab", "command_id": "workspace.switchToPreviousTab"},
            {"id": "nav.tab_1", "sequence": "ctrl+1", "command_id": "workspace.switchToTab", "args": {"index": 0}},
            {"id": "nav.tab_2", "sequence": "ctrl+2", "command_id": "workspace.switchToTab", "args": {"index": 1}},
            {"id": "nav.tab_3", "sequence": "ctrl+3", "command_id": "workspace.switchToTab", "args": {"index": 2}},
            
            # Terminal operations
            {"id": "terminal.new", "sequence": "ctrl+shift+`", "command_id": "terminal.newTerminal"},
            {"id": "terminal.kill", "sequence": "ctrl+shift+k", "command_id": "terminal.killActiveTerminal"},
        ]


class VimKeymapProvider(KeymapProvider):
    """Vim-style keymap provider."""
    
    def get_info(self) -> KeymapInfo:
        """Get Vim keymap info."""
        return KeymapInfo(
            id="vim",
            name="Vim",
            description="Vim-style keyboard shortcuts",
            version="1.0"
        )
    
    def get_shortcuts(self) -> List[Dict[str, Any]]:
        """Get Vim shortcuts."""
        return [
            # File operations (using leader key approach)
            {"id": "file.new", "sequence": "ctrl+n", "command_id": "file.newEditorTab"},
            {"id": "file.open", "sequence": "ctrl+o", "command_id": "file.open"},
            {"id": "file.save", "sequence": "ctrl+s", "command_id": "file.save", "when": "!vimMode"},
            {"id": "file.save_vim", "sequence": "space w", "command_id": "file.save", "when": "vimMode"},
            {"id": "file.quit", "sequence": "space q", "command_id": "file.closeActiveTab", "when": "vimMode"},
            
            # Edit operations
            {"id": "edit.cut", "sequence": "ctrl+x", "command_id": "editor.cut", "when": "!vimMode"},
            {"id": "edit.copy", "sequence": "ctrl+c", "command_id": "editor.copy", "when": "!vimMode"},
            {"id": "edit.paste", "sequence": "ctrl+v", "command_id": "editor.paste", "when": "!vimMode"},
            {"id": "edit.undo", "sequence": "u", "command_id": "editor.undo", "when": "vimMode && vimNormalMode"},
            {"id": "edit.redo", "sequence": "ctrl+r", "command_id": "editor.redo", "when": "vimMode && vimNormalMode"},
            
            # View operations
            {"id": "view.sidebar", "sequence": "space e", "command_id": "view.toggleSidebar", "when": "vimMode"},
            {"id": "view.terminal", "sequence": "space t", "command_id": "view.toggleTerminal", "when": "vimMode"},
            
            # Workspace operations with vim-style navigation
            {"id": "workspace.split_horizontal", "sequence": "space s", "command_id": "workspace.splitActivePane", "args": {"orientation": "horizontal"}, "when": "vimMode"},
            {"id": "workspace.split_vertical", "sequence": "space v", "command_id": "workspace.splitActivePane", "args": {"orientation": "vertical"}, "when": "vimMode"},
            {"id": "workspace.focus_left", "sequence": "space h", "command_id": "workspace.navigateToPreviousPane", "when": "vimMode"},
            {"id": "workspace.focus_right", "sequence": "space l", "command_id": "workspace.navigateToNextPane", "when": "vimMode"},
            
            # Buffer/tab navigation
            {"id": "nav.next_buffer", "sequence": "space b n", "command_id": "workspace.switchToNextTab", "when": "vimMode"},
            {"id": "nav.prev_buffer", "sequence": "space b p", "command_id": "workspace.switchToPreviousTab", "when": "vimMode"},
        ]


class KeymapManager:
    """Manages keyboard keymaps and switching between them."""
    
    def __init__(self, registry: ShortcutRegistry):
        """Initialize the keymap manager."""
        self._registry = registry
        self._providers: Dict[str, KeymapProvider] = {}
        self._current_keymap: Optional[str] = None
        
        # Register built-in providers
        self._register_builtin_providers()
    
    def _register_builtin_providers(self) -> None:
        """Register built-in keymap providers."""
        self.register_provider(DefaultKeymapProvider())
        self.register_provider(VSCodeKeymapProvider())
        self.register_provider(VimKeymapProvider())
    
    def register_provider(self, provider: KeymapProvider) -> None:
        """Register a keymap provider."""
        info = provider.get_info()
        self._providers[info.id] = provider
        logger.debug(f"Registered keymap provider: {info.name}")
    
    def get_available_keymaps(self) -> List[KeymapInfo]:
        """Get list of available keymaps."""
        keymaps = []
        for provider in self._providers.values():
            keymaps.append(provider.get_info())
        return keymaps
    
    def get_current_keymap(self) -> Optional[str]:
        """Get current active keymap ID."""
        return self._current_keymap
    
    def set_keymap(self, keymap_id: str) -> bool:
        """
        Set the active keymap.
        
        Args:
            keymap_id: ID of keymap to activate
            
        Returns:
            True if keymap was set successfully
        """
        if keymap_id not in self._providers:
            logger.error(f"Unknown keymap: {keymap_id}")
            return False
        
        # Clear current keymap shortcuts
        if self._current_keymap:
            self._clear_keymap_shortcuts(self._current_keymap)
        
        # Load new keymap shortcuts
        provider = self._providers[keymap_id]
        shortcuts = provider.get_shortcuts()
        
        success_count = 0
        for shortcut_data in shortcuts:
            try:
                shortcut_id = f"{keymap_id}.{shortcut_data['id']}"
                
                success = self._registry.register_from_string(
                    shortcut_id=shortcut_id,
                    sequence_str=shortcut_data['sequence'],
                    command_id=shortcut_data['command_id'],
                    when=shortcut_data.get('when'),
                    description=shortcut_data.get('description'),
                    source="keymap",
                    priority=50  # Default priority for keymap shortcuts
                )
                
                if success:
                    success_count += 1
                    # Set args if provided
                    if 'args' in shortcut_data:
                        shortcut = self._registry.get_shortcut(shortcut_id)
                        if shortcut:
                            # Store args in shortcut for later use
                            shortcut._args = shortcut_data['args']
                
            except Exception as e:
                logger.error(f"Failed to register shortcut {shortcut_data}: {e}")
        
        self._current_keymap = keymap_id
        logger.info(f"Activated keymap '{keymap_id}' with {success_count}/{len(shortcuts)} shortcuts")
        
        return success_count > 0
    
    def _clear_keymap_shortcuts(self, keymap_id: str) -> None:
        """Clear shortcuts from a specific keymap."""
        shortcuts_to_remove = []
        
        for shortcut in self._registry.get_all_shortcuts():
            if shortcut.id.startswith(f"{keymap_id}."):
                shortcuts_to_remove.append(shortcut.id)
        
        for shortcut_id in shortcuts_to_remove:
            self._registry.unregister(shortcut_id)
        
        logger.debug(f"Cleared {len(shortcuts_to_remove)} shortcuts from keymap '{keymap_id}'")
    
    def export_keymap(self, keymap_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a keymap to a dictionary format.
        
        Args:
            keymap_id: ID of keymap to export
            
        Returns:
            Keymap data or None if not found
        """
        if keymap_id not in self._providers:
            return None
        
        provider = self._providers[keymap_id]
        info = provider.get_info()
        shortcuts = provider.get_shortcuts()
        
        return {
            "info": {
                "id": info.id,
                "name": info.name,
                "description": info.description,
                "version": info.version,
                "author": info.author
            },
            "shortcuts": shortcuts
        }
    
    def import_keymap_from_dict(self, keymap_data: Dict[str, Any]) -> bool:
        """
        Import a keymap from dictionary data.
        
        Args:
            keymap_data: Keymap data dictionary
            
        Returns:
            True if imported successfully
        """
        try:
            info_data = keymap_data.get("info", {})
            shortcuts_data = keymap_data.get("shortcuts", [])
            
            # Create keymap info
            info = KeymapInfo(
                id=info_data.get("id", "imported"),
                name=info_data.get("name", "Imported Keymap"),
                description=info_data.get("description", ""),
                version=info_data.get("version", "1.0"),
                author=info_data.get("author", "Unknown"),
                shortcuts=shortcuts_data
            )
            
            # Create custom provider
            class CustomKeymapProvider(KeymapProvider):
                def __init__(self, keymap_info):
                    self._info = keymap_info
                
                def get_info(self) -> KeymapInfo:
                    return self._info
                
                def get_shortcuts(self) -> List[Dict[str, Any]]:
                    return self._info.shortcuts
            
            # Register provider
            provider = CustomKeymapProvider(info)
            self.register_provider(provider)
            
            logger.info(f"Imported keymap: {info.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import keymap: {e}")
            return False
    
    def load_keymap_from_file(self, file_path: str) -> bool:
        """
        Load a keymap from a JSON file.
        
        Args:
            file_path: Path to keymap file
            
        Returns:
            True if loaded successfully
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                keymap_data = json.load(f)
            
            return self.import_keymap_from_dict(keymap_data)
            
        except Exception as e:
            logger.error(f"Failed to load keymap from {file_path}: {e}")
            return False
    
    def save_keymap_to_file(self, keymap_id: str, file_path: str) -> bool:
        """
        Save a keymap to a JSON file.
        
        Args:
            keymap_id: ID of keymap to save
            file_path: Path to save keymap file
            
        Returns:
            True if saved successfully
        """
        try:
            keymap_data = self.export_keymap(keymap_id)
            if not keymap_data:
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(keymap_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved keymap '{keymap_id}' to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save keymap to {file_path}: {e}")
            return False