#!/usr/bin/env python3
# quiet_interface_rag.py - Extension of quiet_interface.py with RAG support

import os
import sys
import http.server
import socketserver
import json
import urllib.parse
from pathlib import Path
import threading
import webbrowser
import time
import logging
import traceback

# Base directory - use absolute path
BASE_DIR = Path("/Volumes/LLM")

# Ensure rag_support module is in path
rag_support_dir = str(BASE_DIR / "rag_support")
if rag_support_dir not in sys.path:
    sys.path.append(rag_support_dir)

# Ensure scripts directory is in path
scripts_dir = str(BASE_DIR / "scripts")
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

# Import the original quiet_interface
try:
    import quiet_interface
    from quiet_interface import find_models, HTML_TEMPLATE, START_PORT, END_PORT
except ImportError:
    print("Error: Could not import quiet_interface module")
    sys.exit(1)

# Import RAG support modules
try:
    import rag_support
    from rag_support.api_extensions import api_handler
    from rag_support.ui_extensions import get_extended_html_template
    from rag_support.utils import project_manager, search_engine
except ImportError:
    print("Error: Could not import rag_support modules")
    traceback.print_exc()
    sys.exit(1)

# Get the extended HTML template with RAG support
HTML_TEMPLATE_WITH_RAG = get_extended_html_template()

class RagRequestHandler(quiet_interface.RequestHandler):
    """Handler for HTTP requests with RAG support"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Handle API requests for RAG support
        if parsed_path.path.startswith('/api/projects'):
            query_params = {}
            if parsed_path.query:
                query_params = {k: v[0] for k, v in urllib.parse.parse_qs(parsed_path.query).items()}
            
            status_code, response_data = api_handler.handle_request(
                parsed_path.path, 
                'GET', 
                query_params=query_params
            )
            
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
        
        # Handle main page with RAG support
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE_WITH_RAG.encode('utf-8'))
            return
        
        # For other requests, use the original handler
        return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Handle API requests for RAG support
        if parsed_path.path.startswith('/api/projects'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            status_code, response_data = api_handler.handle_request(
                parsed_path.path, 
                'POST', 
                body=request_data
            )
            
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
        
        # Handle chat requests with context
        if parsed_path.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Check if this is a RAG request with context documents
            context_docs = request_data.get('context_docs', [])
            
            # If no context docs, use the original handler
            if not context_docs:
                return super().do_POST()
            
            # Handle chat with context
            model_path = request_data.get('model', '')
            message = request_data.get('message', '')
            system_message = request_data.get('system', '')
            temperature = request_data.get('temperature', 0.7)
            max_tokens = request_data.get('max_tokens', 1024)
            top_p = request_data.get('top_p', 0.95)
            frequency_penalty = request_data.get('frequency_penalty', 0.0)
            presence_penalty = request_data.get('presence_penalty', 0.0)
            
            # Extract context from documents
            context_content = ''
            project_id = None
            
            # Find the project ID from the first document
            if context_docs and len(context_docs) > 0:
                # Try to determine project from HTTP referer
                referer = self.headers.get('Referer', '')
                referer_parts = urllib.parse.urlparse(referer).path.split('/')
                for i, part in enumerate(referer_parts):
                    if part == 'projects' and i + 1 < len(referer_parts):
                        project_id = referer_parts[i + 1]
                        break
                
                # If we still don't have a project ID, check available projects
                if not project_id:
                    projects = project_manager.get_projects()
                    if projects:
                        # Use the first project
                        project_id = projects[0]['id']
            
            # If we have a project ID, get the document content
            if project_id:
                for doc_id in context_docs:
                    doc = project_manager.get_document(project_id, doc_id)
                    if doc:
                        context_content += f"## {doc.get('title', 'Document')}\n\n"
                        context_content += doc.get('content', '') + "\n\n"
            
            # Add context to system message if available
            if context_content:
                if system_message:
                    system_message += "\n\n"
                system_message += "Use the following information to answer the user's question:\n\n" + context_content
            
            # Try to use the inference module
            try:
                import minimal_inference_quiet as minimal_inference
                
                # Generate response using the quiet inference module
                result = minimal_inference.generate(
                    model_path=model_path,
                    prompt=message,
                    system_prompt=system_message,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty
                )
                
                # If there was an error, return it
                if "error" in result:
                    response = {
                        "error": result['error'],
                        "model": model_path
                    }
                else:
                    # Return the successful response with context info
                    response = {
                        "response": result['response'],
                        "model": model_path,
                        "time_taken": result.get('time_taken', 'N/A'),
                        "tokens_generated": result.get('tokens_generated', 'N/A'),
                        "context_used": True,
                        "context_count": len(context_docs)
                    }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
                
            except Exception as e:
                import traceback
                response = {
                    "error": f"Error generating response: {str(e)}",
                    "model": model_path
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
        
        # For other requests, use the original handler
        return super().do_POST()

def open_browser(port):
    """Open the browser after a short delay"""
    time.sleep(1)
    webbrowser.open(f'http://localhost:{port}')

if __name__ == '__main__':
    print(f"Starting RAG-enhanced LLM interface...")
    
    # Try to find an available port
    for port in range(START_PORT, END_PORT + 1):
        try:
            # Set up the server with RAG-enhanced request handler
            httpd = socketserver.TCPServer(("", port), RagRequestHandler)
            print(f"Server running on port {port}")
            print(f"Open your browser to http://localhost:{port}")
            
            # Open browser in a separate thread
            threading.Thread(target=open_browser, args=(port,)).start()
            
            # Start the server
            httpd.serve_forever()
        except OSError:
            print(f"Port {port} is in use, trying next port...")
        except KeyboardInterrupt:
            print("Server stopped by user")
            sys.exit(0)
    
    print("Could not find an available port")
    sys.exit(1)