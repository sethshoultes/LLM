#!/usr/bin/env python3
"""
Modern web interface for the LLM Platform.

Provides a web interface for the LLM Platform using the modernized
web server, routing, middleware, and handler systems.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Set up basic environment variables
os.environ["LLAMA_CPP_VERBOSE"] = "0"  # Suppress llama.cpp debug logs

# Get base directory from environment or use script location
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
# Use environment variable if available
BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(BASE_DIR)))

# Ensure base directories exist
BASE_DIR.mkdir(exist_ok=True)

# Ensure PYTHONPATH includes necessary directories
for path in [str(BASE_DIR), str(SCRIPT_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Parse command line arguments
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="LLM Platform Web Interface")
    parser.add_argument("--port", type=int, default=5100,
                      help="Port to run the web server on")
    parser.add_argument("--host", default="localhost",
                      help="Host to run the web server on")
    parser.add_argument("--rag", action="store_true",
                      help="Enable RAG features")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug mode")
    parser.add_argument("--no-browser", action="store_true",
                      help="Don't open browser automatically")
    
    return parser.parse_args()

# Process command line arguments
args = parse_args()

# Set environment variables based on arguments
if args.rag:
    os.environ["LLM_RAG_ENABLED"] = "1"
    
if args.debug:
    os.environ["LLM_DEBUG_MODE"] = "1"

# Check for environment flags
RAG_ENABLED = os.environ.get("LLM_RAG_ENABLED") == "1"
DEBUG_MODE = os.environ.get("LLM_DEBUG_MODE") == "1"

# Configure logging based on debug mode
if DEBUG_MODE:
    logging.basicConfig(level=logging.DEBUG, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print("Debug mode is enabled - showing detailed logs")
else:
    logging.basicConfig(level=logging.INFO)

# Import models handling
try:
    import minimal_inference_quiet as inference
    HAS_INFERENCE = True
except ImportError:
    print("Warning: minimal_inference_quiet.py not found. Some features may not work.")
    HAS_INFERENCE = False

# Import RAG components if enabled
if RAG_ENABLED:
    try:
        from rag_support.api_extensions import api_handler as rag_api_handler
        HAS_RAG = True
        print("RAG features enabled")
    except ImportError:
        print("Warning: RAG support modules not found. RAG features will be disabled.")
        HAS_RAG = False
else:
    HAS_RAG = False
    
# Import web modules
try:
    from web.server import create_server, start_server
    from web.router import Router
    from web.middleware import request_logger, response_logger, static_files, json_body_parser, cors_headers
    from web.handlers import render_view, json_api, redirect
except ImportError as e:
    print(f"Error importing web modules: {e}")
    print("Please ensure web modules are installed.")
    sys.exit(1)

# Create router
router = Router()

# Define routes

# Main route
@router.get("/")
def index(request, response):
    """Render the main interface page."""
    # Get available models
    models = []
    if HAS_INFERENCE:
        try:
            models = inference.list_models()
        except Exception as e:
            logging.error(f"Error listing models: {e}")
            models = []
    
    # Render template
    return render_view("layouts/main.html", {
        "title": "LLM Interface",
        "models": models,
        "rag_enabled": RAG_ENABLED,
        "debug_mode": DEBUG_MODE
    })(request, response)

# Static files route
@router.get("/assets/{file_path}")
def assets(request, response):
    """Serve static assets."""
    file_path = request.path_params.get("file_path", "")
    static_dir = BASE_DIR / "templates" / "assets"
    
    # Determine the full path
    full_path = static_dir / file_path
    
    # Check if file exists
    if not full_path.is_file():
        return response.error(404, "File not found")
    
    # Determine MIME type
    import mimetypes
    content_type, _ = mimetypes.guess_type(str(full_path))
    if not content_type:
        content_type = "application/octet-stream"
    
    # Read file
    try:
        with open(full_path, "rb") as f:
            content = f.read()
        
        # Set response
        response.set_content_type(content_type)
        response.body = content
    except Exception as e:
        logging.error(f"Error reading file {full_path}: {e}")
        response.error(500, "Error reading file")

# API Routes

# List models API
@router.get("/api/models")
def api_list_models(request, response):
    """List available models API endpoint."""
    try:
        if not HAS_INFERENCE:
            return response.json({"error": "Inference module not available"}, 500)
        
        models = inference.list_models()
        response.json({"models": models})
    except Exception as e:
        logging.error(f"Error listing models: {e}")
        response.json({"error": str(e)}, 500)

# Generate text API
@router.post("/api/generate")
def api_generate(request, response):
    """Generate text API endpoint."""
    try:
        if not HAS_INFERENCE:
            return response.json({"error": "Inference module not available"}, 500)
        
        # Get request data
        data = request.body
        if not isinstance(data, dict):
            return response.json({"error": "Invalid request data"}, 400)
        
        # Extract parameters
        model_path = data.get("model")
        prompt = data.get("prompt")
        system_prompt = data.get("system_prompt", "")
        temperature = data.get("temperature", 0.7)
        max_tokens = data.get("max_tokens", 500)
        top_p = data.get("top_p", 0.9)
        
        # Validate required parameters
        if not model_path:
            return response.json({"error": "Model path is required"}, 400)
        
        if not prompt:
            return response.json({"error": "Prompt is required"}, 400)
        
        # Generate text
        result = inference.generate(
            model_path=model_path,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        
        # Check for error
        if "error" in result:
            return response.json({
                "error": result["error"],
                "success": False
            }, 500)
        
        # Return result
        response.json({
            "response": result["response"],
            "model": model_path,
            "tokens_generated": result.get("tokens_generated", 0),
            "time_taken": result.get("time_taken", 0),
            "success": True
        })
    except Exception as e:
        logging.error(f"Error generating text: {e}")
        response.json({"error": str(e), "success": False}, 500)

# RAG API routes
if HAS_RAG:
    @router.all("/api/projects{path:.*}")
    def rag_api(request, response):
        """Handle RAG API requests."""
        try:
            # Get full path
            full_path = f"/api/projects{request.path_params.get('path', '')}"
            
            # Process query parameters
            query_params = request.query_params
            
            # Get request body
            body = request.body
            
            # Call RAG API handler
            status_code, result = rag_api_handler.handle_request(
                path=full_path,
                method=request.method,
                query_params=query_params,
                body=body
            )
            
            # Set response
            response.status_code = status_code
            response.json(result)
        except Exception as e:
            logging.error(f"Error handling RAG API request: {e}")
            response.json({
                "error": str(e),
                "status": 500
            }, 500)

# Create middleware stack
middleware = [
    request_logger,
    response_logger,
    json_body_parser,
    cors_headers(allow_origin="*"),
    static_files(static_dir=BASE_DIR / "templates" / "assets", url_prefix="/assets")
]

# Create and start server
def main():
    """Start the web server."""
    # Log configuration
    logging.info(f"BASE_DIR: {BASE_DIR}")
    logging.info(f"RAG_ENABLED: {RAG_ENABLED}")
    logging.info(f"DEBUG_MODE: {DEBUG_MODE}")
    
    # Create server config
    server_config = {
        "host": args.host,
        "port": args.port,
        "router": router,
        "middleware": middleware,
        "open_browser": not args.no_browser
    }
    
    try:
        # Create and start server
        server = create_server(**server_config)
        host, port = server.start(block=True)
        
        logging.info(f"Server started on http://{host}:{port}")
        if not args.no_browser:
            logging.info("Opening browser...")
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Error starting server: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()