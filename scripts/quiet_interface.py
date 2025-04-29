#!/usr/bin/env python3
# quiet_interface.py - Minimal interface with suppressed debug logs

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

# Error handling utilities
class ErrorHandler:
    """Centralized error handling with consistent formatting and logging"""
    
    @staticmethod
    def format_error(error, include_traceback=False):
        """Format an error message with optional traceback"""
        error_type = type(error).__name__
        error_message = str(error)
        
        formatted = f"Error: {error_type} - {error_message}"
        
        if include_traceback:
            tb = traceback.format_exc()
            formatted += f"\n\nTraceback:\n{tb}"
            
        return formatted
    
    @staticmethod
    def log_error(error, context="", level=logging.ERROR, include_traceback=False):
        """Log an error with consistent formatting"""
        logger = logging.getLogger("llm_interface")
        
        if context:
            message = f"[{context}] {ErrorHandler.format_error(error, include_traceback=False)}"
        else:
            message = ErrorHandler.format_error(error, include_traceback=False)
            
        logger.log(level, message)
        
        if include_traceback:
            logger.debug(f"Traceback for error in {context or 'unknown context'}:\n{traceback.format_exc()}")
    
    @staticmethod
    def handle_api_error(error, context="", include_traceback=False):
        """Format an error for API response"""
        ErrorHandler.log_error(error, context, include_traceback=include_traceback)
        
        response = {
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context
        }
        
        if include_traceback:
            response["traceback"] = traceback.format_exc()
            
        return response
    
    @staticmethod
    def handle_request_error(handler, status_code, error, context=""):
        """Handle an error during request processing"""
        ErrorHandler.log_error(error, context, include_traceback=DEBUG_MODE)
        
        handler.send_error(
            status_code, 
            explain=ErrorHandler.format_error(error, include_traceback=False)
        )

# Disable debug logs
os.environ["LLAMA_CPP_VERBOSE"] = "0"  # Suppress llama.cpp debug logs

# Import jinja2 for templating
try:
    import jinja2
except ImportError:
    print("Jinja2 not installed. Please install with: pip install jinja2")
    jinja2 = None

# Define the port range to try
START_PORT = 5100
END_PORT = 5110

# Get base directory from environment or use script location
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
# Use environment variable if available
BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(BASE_DIR)))

# Set up template directories
TEMPLATES_DIR = BASE_DIR / "templates"
LAYOUTS_DIR = TEMPLATES_DIR / "layouts"
COMPONENTS_DIR = TEMPLATES_DIR / "components"
ASSETS_DIR = TEMPLATES_DIR / "assets"

# Set up Jinja2 environment if available
if jinja2:
    try:
        template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATES_DIR)
        template_env = jinja2.Environment(loader=template_loader)
        print(f"Template directory: {TEMPLATES_DIR}")
    except Exception as e:
        print(f"Error setting up Jinja2: {e}")
        template_env = None
else:
    template_env = None

# Check for environment flags
RAG_ENABLED = os.environ.get("LLM_RAG_ENABLED") == "1"
DEBUG_MODE = os.environ.get("LLM_DEBUG_MODE") == "1"

# Configure logging based on debug mode
if DEBUG_MODE:
    logging.basicConfig(level=logging.DEBUG, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    print("Debug mode is enabled - showing detailed logs")
else:
    logging.basicConfig(level=logging.ERROR)

# Setup paths
try:
    # Ensure base directories exist
    BASE_DIR.mkdir(exist_ok=True)
    
    # Ensure PYTHONPATH includes necessary directories
    for path in [str(BASE_DIR), str(SCRIPT_DIR)]:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # Log configuration details when in debug mode
    if DEBUG_MODE:
        print(f"BASE_DIR: {BASE_DIR}")
        print(f"SCRIPT_DIR: {SCRIPT_DIR}")
        print(f"RAG_ENABLED: {RAG_ENABLED}")
        print(f"DEBUG_MODE: {DEBUG_MODE}")
        print(f"sys.path: {sys.path}")
except Exception as e:
    print(f"Error during path setup: {e}")
    if DEBUG_MODE:
        traceback.print_exc()

# Template rendering function
def render_template(template_name, **kwargs):
    """Render a template with the given kwargs
    
    Falls back to the static HTML template if Jinja2 is not available or if
    the template file is not found.
    """
    if not template_env:
        # Log warning about using fallback HTML
        print("Warning: Jinja2 not available, using fallback HTML template")
        return get_fallback_html(RAG_ENABLED)
    
    try:
        # Try to load the template
        template = template_env.get_template(template_name)
        return template.render(**kwargs)
    except jinja2.exceptions.TemplateNotFound:
        print(f"Warning: Template {template_name} not found, using fallback HTML")
        return get_fallback_html(RAG_ENABLED)
    except Exception as e:
        print(f"Error rendering template {template_name}: {e}")
        if DEBUG_MODE:
            traceback.print_exc()
        return get_fallback_html(RAG_ENABLED)

# Fallback HTML template for when templates or Jinja2 are not available
def get_fallback_html(rag_enabled=False):
    """Get the fallback HTML template
    
    This is used when Jinja2 is not available or if template files are not found.
    """
    if rag_enabled and RAG_ENABLED:
        try:
            from rag_support.ui_extensions import get_extended_html_template
            return get_extended_html_template()
        except ImportError:
            print("Error loading RAG UI extensions, using standard template")
            return HTML_TEMPLATE
        except Exception as e:
            print(f"Error applying RAG extensions: {e}")
            return HTML_TEMPLATE
    else:
        return HTML_TEMPLATE

# HTML template for the main page (fallback if templates are unavailable)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Interface</title>
    <!-- EXTENSION_POINT: HEAD -->
    <style>
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem;
            background-color: #f5f7f9;
        }
        .card {
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 2rem;
            margin-bottom: 2rem;
        }
        h1, h2, h3 {
            margin-top: 0;
            color: #2a2a2a;
        }
        pre {
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 4px;
            overflow: auto;
        }
        button {
            background-color: #0070f3;
            color: white;
            border: none;
            padding: 0.8rem 1.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: #0051a2;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .model-list {
            margin-top: 1rem;
        }
        .model-item {
            padding: 0.8rem;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .model-info {
            flex: 1;
        }
        textarea {
            width: 100%;
            height: 100px;
            padding: 0.8rem;
            border-radius: 4px;
            border: 1px solid #ddd;
            margin-bottom: 1rem;
            font-family: inherit;
            font-size: 1rem;
            resize: vertical;
        }
        .response {
            background-color: #f9f9f9;
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 4px solid #0070f3;
            margin-top: 1rem;
            white-space: pre-wrap;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(0,0,0,.1);
            border-radius: 50%;
            border-top-color: #0070f3;
            animation: spin 1s ease-in-out infinite;
            margin-left: 10px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .stats {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.5rem;
        }
        select {
            width: 100%;
            padding: 0.8rem;
            border-radius: 4px;
            border: 1px solid #ddd;
            margin-bottom: 1rem;
            font-size: 1rem;
        }
        .parameter-controls {
            background: #f5f7f9;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .parameter-row {
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
        }
        .parameter-row label {
            width: 40%;
            font-size: 0.9rem;
        }
        .parameter-row input[type="range"] {
            flex: 1;
        }
        .chat-history {
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: 1rem;
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 1rem;
            background: #fafafa;
        }
        .chat-message {
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #eee;
        }
        .chat-message:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }
        .message-user {
            background-color: #f0f7ff;
            border-radius: 8px;
            padding: 0.8rem;
            margin-bottom: 0.5rem;
        }
        .message-assistant {
            background-color: #f9f9f9;
            border-radius: 8px;
            padding: 0.8rem;
            border-left: 4px solid #0070f3;
            white-space: pre-wrap;
        }
        .message-meta {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.3rem;
            text-align: right;
        }
        .message-input {
            display: flex;
            gap: 0.8rem;
            margin-bottom: 1rem;
        }
        .message-input textarea {
            flex: 1;
            margin-bottom: 0;
        }
        .chat-controls {
            display: flex;
            gap: 0.8rem;
            margin-bottom: 1rem;
        }
        .secondary-btn {
            background-color: #f5f5f5;
            color: #333;
            border: 1px solid #ddd;
            padding: 0.6rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        .secondary-btn:hover {
            background-color: #e9e9e9;
        }
    </style>
</head>
<body>
    <!-- EXTENSION_POINT: HEADER_NAV -->
    <h1>Portable LLM Interface</h1>
    
    <div class="card">
        <h2>Available Models</h2>
        <div id="modelList" class="model-list">Loading models...</div>
    </div>
    <!-- EXTENSION_POINT: SIDEBAR -->
    
    <div class="card">
        <h2>Model Selection</h2>
        <select id="modelSelect">
            <option value="">Select a model</option>
        </select>
        <textarea id="systemInput" placeholder="System message (optional)" style="height: 60px;"></textarea>
    </div>
    
    <div class="card">
        <h2>Chat</h2>
        <!-- EXTENSION_POINT: MAIN_CONTROLS -->
        <div id="chatHistory" class="chat-history"></div>
        
        <div class="message-input">
            <textarea id="userInput" placeholder="Enter your message here..."></textarea>
            <button id="sendBtn">Send</button>
            <div id="spinner" class="loading" style="display: none;"></div>
        </div>
        
        <div class="chat-controls">
            <button id="newChatBtn" class="secondary-btn">New Chat</button>
            <button id="exportChatBtn" class="secondary-btn">Export Chat</button>
            <!-- EXTENSION_POINT: CHAT_CONTROLS -->
        </div>
        
        <div class="parameter-controls">
            <h3>Generation Parameters</h3>
            <div class="parameter-row">
                <label for="temperature">Temperature: <span id="tempValue">0.7</span></label>
                <input type="range" id="temperature" min="0.1" max="2.0" step="0.1" value="0.7" 
                       oninput="document.getElementById('tempValue').textContent = this.value">
            </div>
            <div class="parameter-row">
                <label for="maxTokens">Max Tokens: <span id="tokenValue">1024</span></label>
                <input type="range" id="maxTokens" min="64" max="4096" step="64" value="1024" 
                       oninput="document.getElementById('tokenValue').textContent = this.value">
            </div>
            <div class="parameter-row">
                <label for="topP">Top P: <span id="topPValue">0.95</span></label>
                <input type="range" id="topP" min="0.05" max="1.0" step="0.05" value="0.95" 
                       oninput="document.getElementById('topPValue').textContent = this.value">
            </div>
            <div class="parameter-row">
                <label title="Reduces repetition of token sequences">Frequency Penalty: <span id="freqValue">0.0</span></label>
                <input type="range" id="freqPenalty" min="0.0" max="2.0" step="0.1" value="0.0" 
                       oninput="document.getElementById('freqValue').textContent = this.value">
            </div>
        </div>
        
        <div id="stats" class="stats" style="display: none;"></div>
    </div>
    <!-- EXTENSION_POINT: DIALOGS -->
    
    <script>
        // Initialize chat history
        let chatHistory = [];
        let currentChatId = Date.now().toString();
        
        // Fetch models on page load
        fetch('/api/models')
            .then(response => response.json())
            .then(data => {
                const modelList = document.getElementById('modelList');
                const modelSelect = document.getElementById('modelSelect');
                
                if (data.models && data.models.length > 0) {
                    let html = '';
                    data.models.forEach(model => {
                        html += `<div class="model-item">
                            <div class="model-info">
                                <strong>${model.path.split('/').pop()}</strong><br>
                                <small>
                                    Type: ${model.type}${model.family ? ' | Family: ' + model.family : ''} | 
                                    Format: ${model.format || 'Unknown'} | Size: ${model.size_mb} MB
                                </small>
                            </div>
                        </div>`;
                        
                        const option = document.createElement('option');
                        option.value = model.path;
                        option.textContent = model.path.split('/').pop();
                        modelSelect.appendChild(option);
                    });
                    modelList.innerHTML = html;
                    
                    // Try to load saved chat history
                    loadChatHistory();
                } else {
                    modelList.innerHTML = 'No models found. Download models using: <code>./llm.sh download</code>';
                }
            })
            .catch(error => {
                document.getElementById('modelList').innerHTML = 'Error loading models: ' + error.message;
            });
        
        // Load chat history from localStorage if available
        function loadChatHistory() {
            const savedHistory = localStorage.getItem('llm_chat_history');
            if (savedHistory) {
                try {
                    const savedData = JSON.parse(savedHistory);
                    if (savedData.currentChatId && savedData.chats && savedData.chats[savedData.currentChatId]) {
                        currentChatId = savedData.currentChatId;
                        chatHistory = savedData.chats[currentChatId] || [];
                        renderChatHistory();
                    }
                } catch (e) {
                    console.error('Error loading chat history:', e);
                }
            }
        }
        
        // Save chat history to localStorage
        function saveChatHistory() {
            try {
                const allChats = JSON.parse(localStorage.getItem('llm_chats') || '{}');
                allChats[currentChatId] = chatHistory;
                localStorage.setItem('llm_chats', JSON.stringify(allChats));
                localStorage.setItem('llm_chat_history', JSON.stringify({
                    currentChatId,
                    chats: { [currentChatId]: chatHistory }
                }));
            } catch (e) {
                console.error('Error saving chat history:', e);
            }
        }
        
        // Render chat history in the UI
        function renderChatHistory() {
            const chatHistoryDiv = document.getElementById('chatHistory');
            if (!chatHistory || chatHistory.length === 0) {
                chatHistoryDiv.innerHTML = '<div class="empty-chat">No messages yet. Start a conversation!</div>';
                return;
            }
            
            let html = '';
            chatHistory.forEach(message => {
                const timestamp = new Date(message.timestamp).toLocaleTimeString();
                if (message.role === 'user') {
                    html += `
                        <div class="chat-message">
                            <div class="message-user">${escapeHtml(message.content)}</div>
                            <div class="message-meta">${timestamp}</div>
                        </div>
                    `;
                } else if (message.role === 'assistant') {
                    html += `
                        <div class="chat-message">
                            <div class="message-assistant">${escapeHtml(message.content)}</div>
                            <div class="message-meta">${timestamp}</div>
                        </div>
                    `;
                }
            });
            
            chatHistoryDiv.innerHTML = html;
            
            // Scroll to bottom
            chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
        }
        
        // Helper function to escape HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Add message to chat history
        function addMessageToHistory(role, content) {
            chatHistory.push({
                role,
                content,
                timestamp: Date.now()
            });
            saveChatHistory();
            renderChatHistory();
        }
        
        // Handle send button click
        document.getElementById('sendBtn').addEventListener('click', function() {
            const modelPath = document.getElementById('modelSelect').value;
            const userInput = document.getElementById('userInput').value;
            const systemInput = document.getElementById('systemInput').value;
            const temperature = parseFloat(document.getElementById('temperature').value);
            const maxTokens = parseInt(document.getElementById('maxTokens').value);
            const topP = parseFloat(document.getElementById('topP').value);
            const freqPenalty = parseFloat(document.getElementById('freqPenalty').value);
            const spinner = document.getElementById('spinner');
            const statsDiv = document.getElementById('stats');
            
            if (!modelPath) {
                alert('Please select a model first');
                return;
            }
            
            if (!userInput.trim()) {
                alert('Please enter a message');
                return;
            }
            
            // Add user message to chat history
            addMessageToHistory('user', userInput);
            
            // Clear input field
            document.getElementById('userInput').value = '';
            
            // Show spinner
            spinner.style.display = 'inline-block';
            statsDiv.style.display = 'none';
            
            // Disable send button while processing
            document.getElementById('sendBtn').disabled = true;
            
            // Prepare conversation history for context
            const messages = chatHistory.map(msg => ({
                role: msg.role,
                content: msg.content
            }));
            
            // Send request to API
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: modelPath,
                    message: userInput,
                    system: systemInput,
                    temperature: temperature,
                    max_tokens: maxTokens,
                    top_p: topP,
                    frequency_penalty: freqPenalty,
                    history: messages
                })
            })
            .then(response => response.json())
            .then(data => {
                // Hide spinner
                spinner.style.display = 'none';
                
                if (data.error) {
                    // Add error message to chat
                    addMessageToHistory('assistant', 'Error: ' + data.error);
                } else {
                    // Add assistant message to chat history
                    addMessageToHistory('assistant', data.response || 'No response from model');
                    
                    // Show stats if available
                    if (data.time_taken || data.tokens_generated) {
                        statsDiv.style.display = 'block';
                        let statsText = `Generation time: ${data.time_taken}s | Tokens: ${data.tokens_generated}`;
                        
                        // Add model type and format if available
                        if (data.model_type) {
                            statsText += ` | Type: ${data.model_type}`;
                        }
                        if (data.model_format) {
                            statsText += ` | Format: ${data.model_format}`;
                        }
                        
                        statsDiv.textContent = statsText;
                    }
                }
                
                // Re-enable send button
                document.getElementById('sendBtn').disabled = false;
            })
            .catch(error => {
                spinner.style.display = 'none';
                addMessageToHistory('assistant', 'Error: ' + error.message);
                document.getElementById('sendBtn').disabled = false;
            });
        });
        
        // Handle new chat button
        document.getElementById('newChatBtn').addEventListener('click', function() {
            if (confirm('Start a new chat? This will clear the current conversation.')) {
                chatHistory = [];
                currentChatId = Date.now().toString();
                saveChatHistory();
                renderChatHistory();
                document.getElementById('userInput').value = '';
                document.getElementById('systemInput').value = '';
                document.getElementById('stats').style.display = 'none';
            }
        });
        
        // Handle export chat button
        document.getElementById('exportChatBtn').addEventListener('click', function() {
            if (chatHistory.length === 0) {
                alert('No chat to export');
                return;
            }
            
            const exportData = {
                timestamp: Date.now(),
                model: document.getElementById('modelSelect').value,
                systemPrompt: document.getElementById('systemInput').value,
                messages: chatHistory
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `chat_export_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    </script>
    <!-- EXTENSION_POINT: SCRIPTS -->
</body>
</html>
"""

def find_models():
    """Find all model files in the directory structure"""
    # Try to import the inference module
    try:
        # Make sure the scripts directory is in the path
        scripts_dir = str(BASE_DIR / "scripts")
        if scripts_dir not in sys.path:
            sys.path.append(scripts_dir)
            
        import minimal_inference_quiet as minimal_inference
        
        # Use the module's model listing if available
        models = minimal_inference.list_models()
        print(f"Found {len(models)} models")
        return models
    except ImportError as e:
        print("Could not import minimal_inference module, falling back to basic model search")
        models = []
        
        # Search in quantized directory
        quantized_dir = BASE_DIR / "LLM-MODELS" / "quantized"
        if quantized_dir.exists():
            for format_dir in quantized_dir.glob("*"):
                if format_dir.is_dir():
                    for model_file in format_dir.glob("*"):
                        if model_file.is_file() and model_file.suffix in ['.bin', '.gguf', '.safetensors']:
                            models.append({
                                "path": str(model_file.relative_to(BASE_DIR)),
                                "type": "quantized",
                                "size_mb": round(model_file.stat().st_size / (1024 * 1024), 2)
                            })
        
        # Search in open-source directory
        open_source_dir = BASE_DIR / "LLM-MODELS" / "open-source"
        if open_source_dir.exists():
            for family_dir in open_source_dir.glob("*"):
                if family_dir.is_dir():
                    for size_dir in family_dir.glob("*"):
                        if size_dir.is_dir():
                            for model_file in size_dir.glob("*"):
                                if model_file.is_file() and model_file.suffix in ['.bin', '.gguf', '.safetensors']:
                                    models.append({
                                        "path": str(model_file.relative_to(BASE_DIR)),
                                        "type": "open-source",
                                        "size_mb": round(model_file.stat().st_size / (1024 * 1024), 2)
                                    })
        
        return models

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler for the HTTP requests"""
    
    def log_message(self, format, *args):
        """Override to provide minimal logging"""
        # Mostly silence logging except for errors
        if len(args) > 2 and not args[1].startswith('20'):  # Not a 2xx status code
            super().log_message(format, *args)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Handle RAG API requests if enabled
        if RAG_ENABLED and parsed_path.path.startswith('/api/projects'):
            try:
                # Import the RAG API handler
                from rag_support.api_extensions import api_handler
                
                # Parse query parameters
                query_params = {}
                if parsed_path.query:
                    query_params = {k: v[0] for k, v in urllib.parse.parse_qs(parsed_path.query).items()}
                
                # Handle the request
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
            except ImportError as e:
                ErrorHandler.handle_request_error(
                    self, 500, e, 
                    context=f"RAG API GET (ImportError): {parsed_path.path}"
                )
                return
            except Exception as e:
                ErrorHandler.handle_request_error(
                    self, 500, e, 
                    context=f"RAG API GET: {parsed_path.path}"
                )
                return
        
        # Standard request handling
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Render template or use fallback
            try:
                if template_env:
                    # Use Jinja2 templates
                    html = render_template("layouts/main.html", rag_enabled=RAG_ENABLED)
                    print("Using Jinja2 templates")
                else:
                    # Use fallback template with extension points
                    html = get_fallback_html(RAG_ENABLED)
                    print("Using fallback HTML template")
                
                # Write the HTML response
                self.wfile.write(html.encode('utf-8'))
            except Exception as e:
                error_context = "Rendering main page template"
                ErrorHandler.log_error(e, error_context, include_traceback=DEBUG_MODE)
                self.send_error(500, f"Error rendering template: {str(e)}")
        elif parsed_path.path == '/api/models':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            models = find_models()
            self.wfile.write(json.dumps({"models": models}).encode('utf-8'))
        else:
            self.send_error(404, "File not found")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Handle RAG API requests if enabled
        if RAG_ENABLED and (parsed_path.path.startswith('/api/projects') or parsed_path.path.startswith('/api/tokens')):
            try:
                # Import the RAG API handler
                from rag_support.api_extensions import api_handler
                
                # Read POST data
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
                
                # Handle the request
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
            except ImportError as e:
                ErrorHandler.handle_request_error(
                    self, 500, e, 
                    context=f"RAG API POST (ImportError): {parsed_path.path}"
                )
                return
            except json.JSONDecodeError as e:
                ErrorHandler.handle_request_error(
                    self, 400, e, 
                    context=f"RAG API POST (Invalid JSON): {parsed_path.path}"
                )
                return
            except Exception as e:
                ErrorHandler.handle_request_error(
                    self, 500, e, 
                    context=f"RAG API POST: {parsed_path.path}"
                )
                return
        
        # Standard chat API handling
        if parsed_path.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            model_path = request_data.get('model', '')
            message = request_data.get('message', '')
            system_message = request_data.get('system', '')
            temperature = request_data.get('temperature', 0.7)
            max_tokens = request_data.get('max_tokens', 1024)
            top_p = request_data.get('top_p', 0.95)
            frequency_penalty = request_data.get('frequency_penalty', 0.0)
            presence_penalty = request_data.get('presence_penalty', 0.0)
            message_history = request_data.get('history', [])
            
            # Check for RAG context
            context_docs = request_data.get('context_docs', [])
            context_content = ""
            context_docs_info = []
            max_context_tokens = 1200  # Reserve tokens for system prompt, user message, and response
            
            # Helper function to estimate token count
            def estimate_tokens(text):
                # Roughly 4 chars per token for English text
                return len(text) // 4
            
            # If we have context docs and RAG is enabled, load the document content
            if RAG_ENABLED and context_docs:
                try:
                    from rag_support.utils import project_manager
                    
                    # Find the project ID from the context docs or headers
                    project_id = request_data.get('project_id')
                    
                    # If we don't have a project ID, try to get it from referer
                    if not project_id:
                        referer = self.headers.get('Referer', '')
                        referer_parts = urllib.parse.urlparse(referer).path.split('/')
                        for i, part in enumerate(referer_parts):
                            if part == 'projects' and i + 1 < len(referer_parts):
                                project_id = referer_parts[i + 1]
                                break
                    
                    # If we still don't have a project ID, use the first available project
                    if not project_id:
                        projects = project_manager.get_projects()
                        if projects:
                            project_id = projects[0]['id']
                    
                    # Load documents if we have a project ID
                    if project_id:
                        all_docs = []
                        # First pass: load all documents and calculate token counts
                        for doc_id in context_docs:
                            doc = project_manager.get_document(project_id, doc_id)
                            if doc:
                                doc_content = doc.get('content', '')
                                doc_title = doc.get('title', 'Document')
                                doc_tokens = estimate_tokens(doc_content)
                                all_docs.append({
                                    'id': doc_id,
                                    'title': doc_title,
                                    'content': doc_content,
                                    'tokens': doc_tokens
                                })
                        
                        # Sort by relevance (or token count for now)
                        all_docs.sort(key=lambda x: x['tokens'])
                        
                        # Second pass: add documents until we hit the token limit
                        current_tokens = 0
                        for doc in all_docs:
                            # Check if adding this document would exceed our token limit
                            if current_tokens + doc['tokens'] > max_context_tokens:
                                # If this is the first document, we need to truncate it
                                if len(context_docs_info) == 0:
                                    # Take as much as we can from this document
                                    max_chars = max_context_tokens * 4
                                    truncated_content = doc['content'][:max_chars] + "...[truncated]"
                                    context_content += f"## {doc['title']}\n\n{truncated_content}\n\n"
                                    context_docs_info.append({
                                        'id': doc['id'],
                                        'title': doc['title'],
                                        'tokens': estimate_tokens(truncated_content),
                                        'truncated': True
                                    })
                                    current_tokens += estimate_tokens(truncated_content)
                                break
                            
                            # Add this document to our context
                            context_content += f"## {doc['title']}\n\n{doc['content']}\n\n"
                            context_docs_info.append({
                                'id': doc['id'],
                                'title': doc['title'],
                                'tokens': doc['tokens'],
                                'truncated': False
                            })
                            current_tokens += doc['tokens']
                        
                        # Add context to system message
                        if context_content:
                            if system_message:
                                system_message += "\n\n"
                            system_message += "Use the following information to answer the user's question:\n\n" + context_content
                            
                            print(f"Added {len(context_docs_info)} documents to context. Total tokens: {current_tokens}")
                            for doc in context_docs_info:
                                print(f"- {doc['title']}: {doc['tokens']} tokens {'(truncated)' if doc.get('truncated') else ''}")
                except ImportError as e:
                    print(f"Error loading context: {e}")
                    traceback.print_exc()
                except Exception as e:
                    print(f"Error processing context: {e}")
                    traceback.print_exc()
            
            # Try to use the inference module
            try:
                sys.path.append(str(BASE_DIR / "scripts"))
                # Make sure the scripts directory is in the path
                scripts_dir = str(BASE_DIR / "scripts")
                if scripts_dir not in sys.path:
                    sys.path.append(scripts_dir)
                
                import minimal_inference_quiet as minimal_inference
                print(f"Successfully imported minimal_inference_quiet from {minimal_inference.__file__}")
                
                # Generate response using the quiet inference module with history
                if message_history and len(message_history) > 0:
                    # If we have history, use it for context
                    result = minimal_inference.generate_with_history(
                        model_path=model_path,
                        messages=message_history,
                        system_prompt=system_message,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty
                    )
                else:
                    # Otherwise, use the simple generate function
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
                    # Return the successful response
                    response = {
                        "response": result['response'],
                        "model": model_path,
                        "time_taken": result.get('time_taken', 'N/A'),
                        "tokens_generated": result.get('tokens_generated', 'N/A')
                    }
                    
                    # Add context info if RAG was used
                    if context_docs:
                        response["context_used"] = True
                        response["context_count"] = len(context_docs)
                
            except ImportError as e:
                error_context = "Loading inference module"
                ErrorHandler.log_error(e, context=error_context, include_traceback=DEBUG_MODE)
                response = {
                    "error": f"Error: Could not load inference module. {str(e)}",
                    "error_type": "ImportError",
                    "model": model_path,
                    "recommendation": "Please make sure the required libraries are installed (llama-cpp-python or transformers)"
                }
                if DEBUG_MODE:
                    response["traceback"] = traceback.format_exc()
            except Exception as e:
                error_context = f"Generating response for model {model_path}"
                response = ErrorHandler.handle_api_error(
                    e, 
                    context=error_context, 
                    include_traceback=DEBUG_MODE
                )
                response["model"] = model_path
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint not found")

def open_browser(port):
    """Open the browser after a short delay"""
    time.sleep(1)
    webbrowser.open(f'http://localhost:{port}')

if __name__ == '__main__':
    print(f"Starting LLM interface...")
    
    # Show RAG status
    if RAG_ENABLED:
        print(f"RAG features are enabled.")
        
        # Verify RAG support is accessible
        try:
            # Import and initialize RAG modules - use a context manager to capture import errors
            import importlib
            
            # Try to import rag_support
            try:
                import rag_support
                print(f"RAG support core module loaded successfully")
            except ImportError as e:
                print(f"Critical error: Failed to import rag_support module: {e}")
                if DEBUG_MODE:
                    traceback.print_exc()
                print("Disabling RAG features due to import error")
                RAG_ENABLED = False
                raise ImportError(f"Critical RAG module import error: {e}")
            
            # Try to import utils 
            try:
                from rag_support.utils import project_manager
                print(f"RAG support utility modules loaded successfully")
            except ImportError as e:
                print(f"Error importing RAG utility modules: {e}")
                if DEBUG_MODE:
                    traceback.print_exc()
                
            # Initialize directories
            try:
                result = rag_support.init_directories()
                if result:
                    print(f"RAG directories initialized successfully at {rag_support.BASE_DIR}")
                else:
                    print(f"Warning: RAG directory initialization returned False")
            except Exception as e:
                print(f"Error initializing RAG directories: {e}")
                if DEBUG_MODE:
                    traceback.print_exc()
        except Exception as e:
            print(f"Warning: Error in RAG initialization: {e}")
            print(f"Some RAG features may not work correctly.")
            if DEBUG_MODE:
                traceback.print_exc()
    
    # Try to find an available port
    for port in range(START_PORT, END_PORT + 1):
        try:
            # Set up the server
            httpd = socketserver.TCPServer(("", port), RequestHandler)
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