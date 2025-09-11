#!/usr/bin/env python3
"""
Terminal Asset Bundler
Loads and bundles terminal JavaScript and CSS assets for inline embedding.
"""

import os
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TerminalAssetBundler:
    """Bundles terminal assets (JS/CSS) for inline embedding in HTML."""
    
    def __init__(self):
        """Initialize the asset bundler."""
        self.base_dir = Path(__file__).parent
        self.static_dir = self.base_dir / "static"
        self._cache: Dict[str, str] = {}
        
    def _load_file(self, path: Path) -> str:
        """Load a file from disk with caching."""
        path_str = str(path)
        if path_str not in self._cache:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._cache[path_str] = f.read()
                logger.debug(f"Loaded asset: {path}")
            except Exception as e:
                logger.error(f"Failed to load asset {path}: {e}")
                return ""
        return self._cache[path_str]
    
    def get_xterm_js(self) -> str:
        """Get xterm.js library content."""
        return self._load_file(self.static_dir / "js" / "xterm.js")
    
    def get_xterm_css(self) -> str:
        """Get xterm.css content."""
        return self._load_file(self.static_dir / "css" / "xterm.css")
    
    def get_addon_fit_js(self) -> str:
        """Get xterm-addon-fit.js content."""
        return self._load_file(self.static_dir / "js" / "xterm-addon-fit.js")
    
    def get_addon_weblinks_js(self) -> str:
        """Get xterm-addon-web-links.js content."""
        return self._load_file(self.static_dir / "js" / "xterm-addon-web-links.js")
    
    def get_socketio_js(self) -> str:
        """Get socket.io.min.js content."""
        return self._load_file(self.static_dir / "js" / "socket.io.min.js")
    
    def get_bundled_html(self, session_id: str, port: int) -> str:
        """
        Generate complete HTML with all assets bundled inline.
        
        Args:
            session_id: Terminal session ID
            port: Flask server port for Socket.IO connection
            
        Returns:
            Complete HTML string with embedded assets
        """
        # Load all assets
        xterm_css = self.get_xterm_css()
        xterm_js = self.get_xterm_js()
        addon_fit_js = self.get_addon_fit_js()
        addon_weblinks_js = self.get_addon_weblinks_js()
        socketio_js = self.get_socketio_js()
        
        # Generate HTML with bundled assets
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>Terminal - {session_id}</title>
    <style>
        /* Base terminal styles */
        body {{ 
            margin: 0; 
            padding: 0; 
            overflow: hidden; 
            background: #1e1e1e; 
        }}
        #terminal {{ 
            width: 100%; 
            height: 100vh; 
        }}
        
        /* VSCode-style scrollbars */
        .xterm-viewport::-webkit-scrollbar {{
            width: 10px !important;
        }}
        
        .xterm-viewport::-webkit-scrollbar-track {{
            background: #1e1e1e !important;
        }}
        
        .xterm-viewport::-webkit-scrollbar-thumb {{
            background: #464647 !important;
            border-radius: 5px !important;
        }}
        
        .xterm-viewport::-webkit-scrollbar-thumb:hover {{
            background: #5a5a5c !important;
        }}
        
        /* Bundled xterm.css */
        {xterm_css}
    </style>
</head>
<body>
    <div id="terminal"></div>
    
    <!-- Bundled JavaScript libraries -->
    <script>
        // Socket.IO
        {socketio_js}
    </script>
    
    <script>
        // xterm.js core
        {xterm_js}
    </script>
    
    <script>
        // xterm addons
        {addon_fit_js}
        {addon_weblinks_js}
    </script>
    
    <!-- QWebChannel for Qt communication -->
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    
    <!-- Terminal initialization and theme bridge -->
    <script>
        const SESSION_ID = '{session_id}';
        const SERVER_PORT = {port};
        
        // Terminal instance (global for theme updates)
        let term = null;
        let fitAddon = null;
        
        // Current theme data (will be updated via QWebChannel)
        let currentTheme = {{
            background: '#1e1e1e',
            foreground: '#d4d4d4',
            cursor: '#ffffff',
            cursorAccent: '#000000',
            selection: '#264f78',
            black: '#000000',
            red: '#cd3131',
            green: '#0dbc79',
            yellow: '#e5e510',
            blue: '#2472c8',
            magenta: '#bc3fbc',
            cyan: '#11a8cd',
            white: '#e5e5e5',
            brightBlack: '#666666',
            brightRed: '#f14c4c',
            brightGreen: '#23d18b',
            brightYellow: '#f5f543',
            brightBlue: '#3b8eea',
            brightMagenta: '#d670d6',
            brightCyan: '#29b8db',
            brightWhite: '#e5e5e5'
        }};
        
        // Theme application function
        window.applyTerminalTheme = function(themeData) {{
            console.log('Applying terminal theme:', themeData);
            currentTheme = themeData;
            if (term) {{
                term.setOption('theme', themeData);
            }}
        }};
        
        // Terminal configuration (can be updated via QWebChannel)
        window.terminalConfig = {{
            cursorBlink: true,
            macOptionIsMeta: true,
            scrollback: 1000,
            fontFamily: 'Consolas, "Courier New", monospace',
            fontSize: 14,
            lineHeight: 1.2
        }};
        
        // Initialize terminal
        function initTerminal() {{
            console.log('Initializing terminal with bundled assets...');
            
            try {{
                // Create terminal with current theme
                term = new Terminal({{
                    ...window.terminalConfig,
                    theme: currentTheme,
                    // Performance optimization for Canvas2D
                    rendererType: 'canvas',
                    allowTransparency: false
                }});
                
                // Load addons
                fitAddon = new FitAddon.FitAddon();
                const webLinksAddon = new WebLinksAddon.WebLinksAddon();
                term.loadAddon(fitAddon);
                term.loadAddon(webLinksAddon);
                
                // Open terminal
                term.open(document.getElementById("terminal"));
                
                // Connect to server via Socket.IO
                const socket = io.connect('http://127.0.0.1:' + SERVER_PORT + '/terminal', {{
                    query: {{ session_id: SESSION_ID }}
                }});
                
                // Handle terminal input
                term.onData((data) => {{
                    socket.emit("pty-input", {{ 
                        input: data, 
                        session_id: SESSION_ID 
                    }});
                }});
                
                // Handle server output
                socket.on("pty-output", function (data) {{
                    if (data.session_id === SESSION_ID) {{
                        term.write(data.output);
                    }}
                }});
                
                // Handle resize
                function fitTerminal() {{
                    fitAddon.fit();
                    const dims = {{ 
                        cols: term.cols, 
                        rows: term.rows,
                        session_id: SESSION_ID
                    }};
                    socket.emit("resize", dims);
                }}
                
                // Initial fit
                socket.on("connect", () => {{
                    setTimeout(fitTerminal, 100);
                }});
                
                // Handle window resize
                window.addEventListener('resize', () => {{
                    clearTimeout(window.resizeTimer);
                    window.resizeTimer = setTimeout(fitTerminal, 100);
                }});
                
                // Keyboard shortcuts
                term.attachCustomKeyEventHandler((e) => {{
                    if (e.type !== "keydown") return true;
                    
                    // CRITICAL: Intercept Alt+P for pane navigation
                    // This must be handled at JS level to prevent xterm.js from consuming it
                    if (e.altKey && !e.ctrlKey && !e.shiftKey && e.key.toLowerCase() === "p") {{
                        console.log("Alt+P detected in terminal, notifying Qt");
                        // Notify Qt that Alt+P was pressed
                        if (window.qtTerminal && window.qtTerminal.js_shortcut_pressed) {{
                            window.qtTerminal.js_shortcut_pressed("Alt+P");
                        }}
                        // Prevent xterm.js from seeing this key at all
                        e.preventDefault();
                        e.stopPropagation();
                        return false;  // Critical: Don't let terminal process Alt+P
                    }}
                    
                    // Let Qt handle these global shortcuts - return false to prevent terminal from consuming them
                    if (e.ctrlKey && !e.shiftKey && !e.altKey) {{
                        const key = e.key.toLowerCase();
                        // Global app shortcuts that should bubble up to Qt
                        if (key === "b" ||     // Toggle sidebar
                            key === "\\\\" ||    // Split horizontal
                            key === "t" ||     // Toggle theme
                            key === "n" ||     // New tab
                            key === "w" ||     // Close tab
                            key === "o" ||     // Open file
                            key === "s" ||     // Save file
                            key === "`" ||     // New terminal
                            key === "p") {{    // Command palette
                            return false;  // Don't let terminal consume these
                        }}
                    }}
                    
                    // Let Qt handle Ctrl+Shift+\\ for vertical split
                    if (e.ctrlKey && e.shiftKey && (e.key === "\\\\" || e.key === "|")) {{
                        return false;  // Don't let terminal consume this
                    }}
                    
                    // Terminal-specific shortcuts
                    if (e.ctrlKey && e.shiftKey) {{
                        const key = e.key.toLowerCase();
                        if (key === "v") {{
                            navigator.clipboard.readText().then((text) => {{
                                term.paste(text);
                            }});
                            return false;
                        }} else if (key === "c") {{
                            const selection = term.getSelection();
                            if (selection) {{
                                navigator.clipboard.writeText(selection);
                                return false;
                            }}
                        }}
                    }}
                    
                    return true;  // Let terminal handle everything else
                }});
                
                console.log('Terminal initialized successfully with bundled assets');
                
            }} catch (error) {{
                console.error('Failed to initialize terminal:', error);
                document.getElementById('terminal').innerHTML = 
                    '<div style="color: red; padding: 20px;">Failed to initialize terminal: ' + error.message + '</div>';
            }}
        }}
        
        // Function to focus the terminal (callable from Qt)
        window.focusTerminal = function() {{
            if (term) {{
                term.focus();
                console.log("Terminal focused via Qt request");
            }}
        }};
        
        // QWebChannel setup for Qt communication
        function setupQtBridge() {{
            if (typeof qt !== 'undefined' && qt.webChannelTransport) {{
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    console.log('QWebChannel connected');
                    window.qtTerminal = channel.objects.terminal;
                    
                    // Request initial theme from Qt
                    if (window.qtTerminal && window.qtTerminal.getCurrentTheme) {{
                        window.qtTerminal.getCurrentTheme(function(theme) {{
                            console.log('Received initial theme from Qt:', theme);
                            window.applyTerminalTheme(theme);
                        }});
                    }}
                    
                    // Listen for theme updates
                    if (window.qtTerminal && window.qtTerminal.themeChanged) {{
                        window.qtTerminal.themeChanged.connect(function(theme) {{
                            console.log('Theme changed from Qt:', theme);
                            window.applyTerminalTheme(theme);
                        }});
                    }}
                }});
            }} else {{
                console.log('QWebChannel not available, using default theme');
            }}
        }}
        
        // Focus detection for Qt integration
        const terminalElement = document.getElementById("terminal");
        
        // Detect clicks and focus
        terminalElement.addEventListener('click', () => {{
            if (window.qtTerminal && window.qtTerminal.js_terminal_clicked) {{
                window.qtTerminal.js_terminal_clicked();
            }}
        }});
        
        terminalElement.addEventListener('focus', () => {{
            if (window.qtTerminal && window.qtTerminal.js_terminal_focused) {{
                window.qtTerminal.js_terminal_focused();
            }}
        }}, true);
        
        // Make terminal focusable
        terminalElement.setAttribute('tabindex', '0');
        
        // Initialize when ready
        window.addEventListener('load', function() {{
            initTerminal();
            setupQtBridge();
        }});
        
        // Also try immediately
        if (document.readyState === 'complete') {{
            initTerminal();
            setupQtBridge();
        }}
    </script>
</body>
</html>'''
        
        return html


# Singleton instance
terminal_asset_bundler = TerminalAssetBundler()