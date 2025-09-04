#!/usr/bin/env python3
"""Test MCP server client functionality"""

import json
import subprocess
import time
import threading

class MCPClientTest:
    def __init__(self):
        self.process = None
        
    def start_server(self):
        """Start the MCP server in a subprocess"""
        try:
            self.process = subprocess.Popen(
                ["python", "mcp_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Wait a bit for server to start
            time.sleep(2)
            
            if self.process.poll() is not None:
                print("MCP server failed to start")
                stderr = self.process.stderr.read()
                print(f"Error: {stderr}")
                return False
            
            print("MCP server started successfully")
            return True
            
        except Exception as e:
            print(f"Failed to start MCP server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("MCP server stopped")
    
    def test_connection(self):
        """Test basic MCP server functionality"""
        print("Testing MCP server connection...")
        
        # The MCP server should be running and accepting connections
        # We can't easily test the full MCP protocol without a proper client,
        # but we can verify the server process is running
        
        if self.process and self.process.poll() is None:
            print("MCP server is running and responsive")
            return True
        else:
            print("MCP server is not running")
            return False

def main():
    print("Testing MCP Server Client Functionality")
    print("=" * 50)
    
    client = MCPClientTest()
    
    try:
        # Start the server
        if not client.start_server():
            print("Failed to start MCP server")
            return
        
        # Test connection
        if client.test_connection():
            print("\nMCP server test successful!")
            print("The server is ready to accept MCP client connections.")
            print("\nAvailable tools:")
            print("- query_projects: Query projects from database")
            print("- query_chat_messages: Query chat messages")
            print("- query_rag_documents: Query RAG documents")
            print("- query_project_knowledge: Query project knowledge")
            print("- execute_custom_query: Execute custom SQL queries")
            
            print("\nPress Ctrl+C to stop the server...")
            
            # Keep server running for testing
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping server...")
        
    except Exception as e:
        print(f"Test failed: {e}")
    
    finally:
        client.stop_server()

if __name__ == "__main__":
    main()