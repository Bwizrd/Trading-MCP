#!/usr/bin/env python3
"""
Simple HTTP server to view the comparison HTML page.
"""

import http.server
import socketserver
import webbrowser
import os

PORT = 8888

os.chdir('/Users/paul/Sites/PythonProjects/Trading-MCP')

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"🌐 Server running at http://localhost:{PORT}")
    print(f"📊 Opening compare_bars.html in browser...")
    print(f"\n✅ Press Ctrl+C to stop the server\n")
    
    # Open browser
    webbrowser.open(f"http://localhost:{PORT}/compare_bars.html")
    
    # Keep server running
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
