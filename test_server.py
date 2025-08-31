#!/usr/bin/env python3
"""Simple test server to verify port connectivity"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

def run_test_server():
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Test server is working!')
    
    server = HTTPServer(('127.0.0.1', 8003), SimpleHandler)
    print("Test server running on http://127.0.0.1:8003")
    server.serve_forever()

if __name__ == "__main__":
    run_test_server()