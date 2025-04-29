#!/usr/bin/env python3
# minimal_inference_quiet.py - Simple inference wrapper for LLMs with minimized debug output

import os
import sys
import time
from pathlib import Path

# Suppress llama.cpp debug logs
os.environ["LLAMA_CPP_VERBOSE"] = "0"

# Base directory - use absolute path
BASE_DIR = Path("/Volumes/LLM")

# Global variable to store model instances
loaded_models = {}

class SimpleModelManager:
    """Simple model manager that handles loading and inference"""
    
    def __init__(self):
        self.models = {}
        
    def find_models(self):
        """Find all model files in the directory structure"""
        models = []
        
        # Search in quantized directory
        quantized_dir = BASE_DIR / "LLM-MODELS" / "quantized"
        if quantized_dir.exists():
            for format_dir in quantized_dir.glob("*"):
                if format_dir.is_dir():
                    for model_file in format_dir.glob("*"):
                        if model_file.is_file() and model_file.suffix in ['.bin', '.gguf', '.safetensors']:
                            # Determine model format details
                            model_format = format_dir.name
                            model_ext = model_file.suffix.lower().replace('.', '')
                            
                            # Add format details based on file extension
                            format_details = model_format
                            if model_ext in ['gguf', 'ggml', 'safetensors', 'bin', 'pt']:
                                format_details = f"{model_format} ({model_ext})"
                                
                            # Try to determine the model type from the filename
                            model_family = "unknown"
                            for family in ["llama", "mistral", "tinyllama", "phi", "mixtral", "gemma", "gpt"]:
                                if family in model_file.name.lower():
                                    model_family = family
                                    break
                                    
                            models.append({
                                "path": str(model_file.relative_to(BASE_DIR)),
                                "type": "quantized",
                                "format": format_details,
                                "family": model_family,
                                "full_path": str(model_file),
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
                                    # Determine model format details
                                    model_ext = model_file.suffix.lower().replace('.', '')
                                    
                                    # Add format details based on file extension
                                    format_details = model_ext
                                    if model_ext in ['gguf', 'ggml', 'safetensors', 'bin', 'pt']:
                                        format_details = model_ext.upper()
                                    
                                    models.append({
                                        "path": str(model_file.relative_to(BASE_DIR)),
                                        "type": "open-source",
                                        "format": format_details,
                                        "family": family_dir.name,
                                        "size": size_dir.name,
                                        "full_path": str(model_file),
                                        "size_mb": round(model_file.stat().st_size / (1024 * 1024), 2)
                                    })
        
        return models
    
    def load_model(self, model_path):
        """Load a model from the given path"""
        full_path = str(BASE_DIR / model_path)
        
        # Check if model is already loaded
        if model_path in self.models:
            print(f"Model {model_path} already loaded")
            return True
        
        try:
            print(f"Loading model from {full_path}")
            
            # Check if file exists
            if not os.path.exists(full_path):
                print(f"Model file not found: {full_path}")
                return False
            
            # Determine file extension
            file_ext = os.path.splitext(full_path)[1].lower()
            
            # For GGUF models, use llama-cpp-python
            if file_ext == '.gguf':
                try:
                    from llama_cpp import Llama
                    
                    # Load the model with reasonable defaults
                    model = Llama(
                        model_path=full_path,
                        n_ctx=2048,        # Context window - restored to default
                        n_batch=512        # Batch size
                    )
                    
                    self.models[model_path] = {
                        "model": model,
                        "type": "llama.cpp",
                        "model_format": "gguf",
                        "loaded_at": time.time()
                    }
                    
                    print(f"Successfully loaded GGUF model: {model_path}")
                    return True
                    
                except ImportError:
                    print("llama-cpp-python not installed. Please install with: pip install llama-cpp-python")
                    return False
                except Exception as e:
                    print(f"Error loading GGUF model: {e}")
                    return False
            
            # For GGML models (older format, also using llama-cpp-python)
            elif file_ext == '.ggml' or file_ext == '.bin' and 'ggml' in full_path.lower():
                try:
                    from llama_cpp import Llama
                    
                    # Load the model with reasonable defaults
                    model = Llama(
                        model_path=full_path,
                        n_ctx=2048,        # Context window - restored to default
                        n_batch=512,       # Batch size
                        legacy=True        # Required for GGML models
                    )
                    
                    self.models[model_path] = {
                        "model": model,
                        "type": "llama.cpp",
                        "model_format": "ggml",
                        "loaded_at": time.time()
                    }
                    
                    print(f"Successfully loaded GGML model: {model_path}")
                    return True
                    
                except ImportError:
                    print("llama-cpp-python not installed. Please install with: pip install llama-cpp-python")
                    return False
                except Exception as e:
                    print(f"Error loading GGML model: {e}")
                    return False
            
            # For PyTorch models (safetensors, bin, pt)
            elif file_ext in ['.safetensors', '.bin', '.pt']:
                try:
                    # Check for transformers library
                    import transformers
                    
                    # If it's a full path to a model file, use the parent directory as the model path
                    model_dir = os.path.dirname(full_path) if os.path.isfile(full_path) else full_path
                    
                    # Attempt to load with AutoModelForCausalLM
                    print(f"Loading PyTorch model from {model_dir}")
                    tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir)
                    model = transformers.AutoModelForCausalLM.from_pretrained(
                        model_dir,
                        device_map="auto",  # Use the best available device
                        torch_dtype="auto"  # Automatically choose precision
                    )
                    
                    # Store model, tokenizer and pipeline in the cache
                    self.models[model_path] = {
                        "model": model,
                        "tokenizer": tokenizer,
                        "pipeline": transformers.pipeline(
                            "text-generation",
                            model=model,
                            tokenizer=tokenizer,
                            do_sample=True
                        ),
                        "type": "transformers",
                        "model_format": file_ext.replace('.', ''),
                        "loaded_at": time.time()
                    }
                    
                    print(f"Successfully loaded PyTorch model: {model_path}")
                    return True
                    
                except ImportError:
                    print("Transformers or PyTorch not installed. Please install with: pip install transformers torch")
                    return False
                except Exception as e:
                    print(f"Error loading PyTorch model: {e}")
                    return False
            
            else:
                print(f"Unsupported model format: {file_ext}")
                return False
                
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def generate_text(self, model_path, prompt, system_prompt="", max_tokens=512, temperature=0.7, top_p=0.95, 
                     frequency_penalty=0.0, presence_penalty=0.0):
        """Generate text using the specified model"""
        try:
            # Load model if not already loaded
            if model_path not in self.models:
                success = self.load_model(model_path)
                if not success:
                    return {"error": f"Failed to load model: {model_path}"}
            
            model_info = self.models[model_path]
            model = model_info["model"]
            model_type = model_info["type"]
            
            # For llama-cpp models (both GGUF and GGML)
            if model_type == "llama.cpp":
                full_prompt = ""
                
                # Format the prompt based on model type
                # For TinyLlama, we use the chat template
                if "tinyllama" in model_path.lower():
                    if system_prompt:
                        full_prompt = f"<|system|>\n{system_prompt}</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"
                    else:
                        full_prompt = f"<|user|>\n{prompt}</s>\n<|assistant|>\n"
                # For Mistral, we use a specific format
                elif "mistral" in model_path.lower():
                    if system_prompt:
                        full_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
                    else:
                        full_prompt = f"<s>[INST] {prompt} [/INST]"
                # For Llama models
                elif "llama" in model_path.lower():
                    if system_prompt:
                        full_prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
                    else:
                        full_prompt = f"<s>[INST] {prompt} [/INST]"
                # Generic format for other models
                else:
                    if system_prompt:
                        full_prompt = f"### System:\n{system_prompt}\n\n### User:\n{prompt}\n\n### Assistant:\n"
                    else:
                        full_prompt = f"### User:\n{prompt}\n\n### Assistant:\n"
                
                print(f"Generating with llama.cpp prompt: {full_prompt[:50]}...")
                
                # Generate response
                start_time = time.time()
                
                # Build the parameters dictionary
                generation_params = {
                    "prompt": full_prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "frequency_penalty": frequency_penalty,
                    "presence_penalty": presence_penalty,
                    "stop": ["</s>", "[/INST]", "### User:"],  # Common stop tokens
                }
                
                response = model.create_completion(**generation_params)
                end_time = time.time()
                
                # Extract the generated text
                generated_text = response["choices"][0]["text"].strip()
                
                return {
                    "response": generated_text,
                    "model": model_path,
                    "model_type": model_type,
                    "model_format": model_info.get("model_format", "unknown"),
                    "time_taken": round(end_time - start_time, 2),
                    "tokens_generated": response["usage"]["completion_tokens"],
                    "total_tokens": response["usage"]["total_tokens"]
                }
                
            # For transformers models (PyTorch)
            elif model_type == "transformers":
                pipeline = model_info["pipeline"]
                tokenizer = model_info["tokenizer"]
                
                # Determine if it's a chat model from the model path or structure
                is_chat_model = any(name in model_path.lower() for name in ["chat", "instruct", "dialogue", "convers"])
                
                # Format the prompt based on model type and whether it's a chat model
                if is_chat_model:
                    # For chat models, try to use their respective templates if possible
                    if hasattr(tokenizer, "apply_chat_template") and callable(tokenizer.apply_chat_template):
                        # Use the model's built-in chat template if available
                        messages = []
                        if system_prompt:
                            messages.append({"role": "system", "content": system_prompt})
                        messages.append({"role": "user", "content": prompt})
                        full_prompt = tokenizer.apply_chat_template(messages, tokenize=False)
                    else:
                        # Fallback to a generic template
                        if system_prompt:
                            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"
                        else:
                            full_prompt = f"User: {prompt}\n\nAssistant:"
                else:
                    # For non-chat models, use a simpler prompt format
                    if system_prompt:
                        full_prompt = f"{system_prompt}\n\n{prompt}"
                    else:
                        full_prompt = prompt
                
                print(f"Generating with transformers prompt: {full_prompt[:50]}...")
                
                # Generate response
                start_time = time.time()
                
                # Prepare generation parameters
                gen_kwargs = {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "repetition_penalty": 1.0 + frequency_penalty,  # Convert to repetition penalty format
                    "do_sample": temperature > 0.0,
                }
                
                # Generate the text
                response = pipeline(
                    full_prompt,
                    **gen_kwargs
                )
                
                end_time = time.time()
                
                # Extract the generated text
                if isinstance(response, list) and len(response) > 0:
                    # Extracting the generated text and removing the prompt
                    generated_text = response[0]["generated_text"]
                    
                    # Remove the prompt part from the response if possible
                    if generated_text.startswith(full_prompt):
                        generated_text = generated_text[len(full_prompt):].strip()
                    
                    # Clean up common artifacts
                    if generated_text.startswith(":") or generated_text.startswith("\n"):
                        generated_text = generated_text.lstrip(":\n ")
                else:
                    generated_text = "No response generated"
                
                # Count tokens for stats
                try:
                    input_tokens = len(tokenizer.encode(full_prompt))
                    output_tokens = len(tokenizer.encode(generated_text))
                except:
                    input_tokens = 0
                    output_tokens = 0
                
                return {
                    "response": generated_text,
                    "model": model_path,
                    "model_type": model_type,
                    "model_format": model_info.get("model_format", "unknown"),
                    "time_taken": round(end_time - start_time, 2),
                    "tokens_generated": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
                
            # Unsupported model type
            else:
                return {"error": f"Unsupported model type: {model_type}"}
                
        except Exception as e:
            import traceback
            return {
                "error": f"Error generating text: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    def unload_model(self, model_path):
        """Unload a model to free memory"""
        if model_path in self.models:
            del self.models[model_path]
            import gc
            gc.collect()
            return True
        return False
    
    def unload_all_models(self):
        """Unload all models to free memory"""
        self.models.clear()
        import gc
        gc.collect()
        return True


# Create a global model manager instance
model_manager = SimpleModelManager()

# Add a method to SimpleModelManager to handle conversation history
def format_conversation_history(self, messages, system_prompt="", model_path=""):
    """Format conversation history based on model type and format"""
    
    if not messages:
        return ""
    
    # Get model info if the model is loaded
    model_info = self.models.get(model_path, {})
    model_type = model_info.get("type", "unknown")
    
    # For transformers models with chat capabilities
    if model_type == "transformers" and "tokenizer" in model_info:
        tokenizer = model_info["tokenizer"]
        # Check if the tokenizer has a chat template
        if hasattr(tokenizer, "apply_chat_template") and callable(tokenizer.apply_chat_template):
            chat_messages = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            
            # Convert our message format to the expected format
            for msg in messages:
                role = msg.get('role', '').lower()
                content = msg.get('content', '')
                
                if role in ['user', 'assistant', 'system']:
                    chat_messages.append({"role": role, "content": content})
            
            # Apply the model's built-in chat template
            try:
                return tokenizer.apply_chat_template(chat_messages, tokenize=False)
            except Exception as e:
                print(f"Error applying chat template: {e}")
                # Fall through to the other formatting options
    
    # Otherwise, detect model type from path
    is_tinyllama = "tinyllama" in model_path.lower()
    is_mistral = "mistral" in model_path.lower()
    is_llama = "llama" in model_path.lower() and not is_tinyllama
    
    formatted_messages = []
    
    # Format based on model type
    if is_tinyllama:
        # TinyLlama format
        if system_prompt:
            formatted_messages.append(f"<|system|>\n{system_prompt}</s>")
        
        for msg in messages:
            role = msg.get('role', '').lower()
            content = msg.get('content', '')
            
            if role == 'user':
                formatted_messages.append(f"<|user|>\n{content}</s>")
            elif role == 'assistant':
                formatted_messages.append(f"<|assistant|>\n{content}</s>")
        
        # Add final assistant prompt
        formatted_messages.append("<|assistant|>")
        
    elif is_mistral:
        # Mistral format
        formatted_content = ""
        
        # Add system prompt at the beginning if provided
        if system_prompt:
            formatted_content += f"<s>[INST] {system_prompt}\n\n"
        else:
            formatted_content += "<s>"
        
        # Process messages in pairs (user + assistant)
        for i in range(0, len(messages), 2):
            user_msg = messages[i] if i < len(messages) else None
            assistant_msg = messages[i+1] if i+1 < len(messages) else None
            
            if user_msg and user_msg.get('role') == 'user':
                if i == 0 and system_prompt:
                    # First user message after system prompt
                    formatted_content += f"{user_msg.get('content')} [/INST] "
                else:
                    # Subsequent user messages
                    formatted_content += f"[INST] {user_msg.get('content')} [/INST] "
                
                # Add assistant response if available
                if assistant_msg and assistant_msg.get('role') == 'assistant':
                    formatted_content += f"{assistant_msg.get('content')} "
        
        # If the last message is from a user, add the closing tag
        if messages[-1].get('role') == 'user':
            if len(messages) == 1 and system_prompt:
                formatted_content += f"{messages[-1].get('content')} [/INST]"
            else:
                formatted_content += "[INST] " + messages[-1].get('content') + " [/INST]"
                
        formatted_messages = [formatted_content]
    
    elif is_llama:
        # Llama 2 chat format
        if system_prompt:
            current_content = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n"
        else:
            current_content = "<s>[INST] "
            
        # Track if we need to start a new instruction
        need_inst_tag = False
        
        for i, msg in enumerate(messages):
            role = msg.get('role', '').lower()
            content = msg.get('content', '')
            
            if role == 'user':
                if need_inst_tag:
                    current_content += " [INST] "
                current_content += content
                if i == len(messages) - 1:  # If this is the last message
                    current_content += " [/INST]"
                else:
                    current_content += " [/INST] "
                need_inst_tag = False
            elif role == 'assistant':
                current_content += content + " "
                need_inst_tag = True
        
        formatted_messages = [current_content]
        
    else:
        # Generic format (works for most models)
        if system_prompt:
            formatted_messages.append(f"### System:\n{system_prompt}\n")
        
        for msg in messages:
            role = msg.get('role', '').lower()
            content = msg.get('content', '')
            
            if role == 'user':
                formatted_messages.append(f"### User:\n{content}\n")
            elif role == 'assistant':
                formatted_messages.append(f"### Assistant:\n{content}\n")
        
        # Add final assistant prompt
        formatted_messages.append("### Assistant:\n")
    
    return "\n".join(formatted_messages)

# Add the method to the SimpleModelManager class
SimpleModelManager.format_conversation_history = format_conversation_history

# Simple API for external use
def list_models():
    """List all available models"""
    return model_manager.find_models()

def load_model(model_path):
    """Load a model by path"""
    return model_manager.load_model(model_path)

def generate(model_path, prompt, system_prompt="", max_tokens=512, temperature=0.7, 
           top_p=0.95, frequency_penalty=0.0, presence_penalty=0.0):
    """Generate text using the specified model"""
    return model_manager.generate_text(
        model_path=model_path,
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )

def generate_with_history(model_path, messages, system_prompt="", max_tokens=512, 
                         temperature=0.7, top_p=0.95, frequency_penalty=0.0, presence_penalty=0.0):
    """Generate text using conversation history"""
    try:
        # Load model if not already loaded
        if not model_manager.load_model(model_path):
            return {"error": f"Failed to load model: {model_path}"}
        
        model_info = model_manager.models[model_path]
        model = model_info["model"]
        model_type = model_info.get("type", "unknown")
        
        # Format the conversation history
        formatted_prompt = model_manager.format_conversation_history(
            messages, 
            system_prompt=system_prompt,
            model_path=model_path
        )
        
        print(f"Generating with conversation history: {formatted_prompt[:100]}...")
        
        # For llama.cpp models (GGUF/GGML)
        if model_type == "llama.cpp":
            # Generate response
            start_time = time.time()
            
            # Build the parameters dictionary
            generation_params = {
                "prompt": formatted_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "stop": ["</s>", "[/INST]", "### User:"],  # Common stop tokens
            }
            
            response = model.create_completion(**generation_params)
            end_time = time.time()
            
            # Extract the generated text
            generated_text = response["choices"][0]["text"].strip()
            
            return {
                "response": generated_text,
                "model": model_path,
                "model_type": model_type,
                "model_format": model_info.get("model_format", "unknown"),
                "time_taken": round(end_time - start_time, 2),
                "tokens_generated": response["usage"]["completion_tokens"],
                "total_tokens": response["usage"]["total_tokens"]
            }
            
        # For transformers models (PyTorch)
        elif model_type == "transformers":
            pipeline = model_info["pipeline"]
            tokenizer = model_info["tokenizer"]
            
            # Generate response
            start_time = time.time()
            
            # Prepare generation parameters
            gen_kwargs = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "repetition_penalty": 1.0 + frequency_penalty,  # Convert to repetition penalty format
                "do_sample": temperature > 0.0,
            }
            
            # Generate the text
            response = pipeline(
                formatted_prompt,
                **gen_kwargs
            )
            
            end_time = time.time()
            
            # Extract the generated text
            if isinstance(response, list) and len(response) > 0:
                # Extracting the generated text and removing the prompt
                generated_text = response[0]["generated_text"]
                
                # Remove the prompt part from the response if possible
                if generated_text.startswith(formatted_prompt):
                    generated_text = generated_text[len(formatted_prompt):].strip()
                
                # Clean up common artifacts
                if generated_text.startswith(":") or generated_text.startswith("\n"):
                    generated_text = generated_text.lstrip(":\n ")
            else:
                generated_text = "No response generated"
            
            # Count tokens for stats
            try:
                input_tokens = len(tokenizer.encode(formatted_prompt))
                output_tokens = len(tokenizer.encode(generated_text))
            except:
                input_tokens = 0
                output_tokens = 0
            
            return {
                "response": generated_text,
                "model": model_path,
                "model_type": model_type,
                "model_format": model_info.get("model_format", "unknown"),
                "time_taken": round(end_time - start_time, 2),
                "tokens_generated": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
            
        # Unsupported model type
        else:
            return {"error": f"Unsupported model type for history: {model_type}"}
            
    except Exception as e:
        import traceback
        return {
            "error": f"Error generating text with history: {str(e)}",
            "traceback": traceback.format_exc()
        }

def unload_model(model_path):
    """Unload a specific model"""
    return model_manager.unload_model(model_path)

def unload_all():
    """Unload all models"""
    return model_manager.unload_all_models()

# Test functionality if script is run directly
if __name__ == "__main__":
    # List available models
    print("Available models:")
    models = list_models()
    for i, model in enumerate(models):
        print(f"{i+1}. {model['path']} ({model['size_mb']} MB)")
    
    if models:
        try:
            # Ask user which model to test
            choice = int(input("\nEnter model number to test, or 0 to exit: "))
            if choice > 0 and choice <= len(models):
                model_path = models[choice-1]["path"]
                
                # Test loading the model
                print(f"\nTesting model: {model_path}")
                success = load_model(model_path)
                
                if success:
                    # Test generation
                    prompt = input("\nEnter a prompt: ")
                    if prompt:
                        print("\nGenerating response...")
                        result = generate(model_path, prompt)
                        
                        if "error" in result:
                            print(f"Error: {result['error']}")
                        else:
                            print("\nGenerated response:")
                            print("-" * 40)
                            print(result["response"])
                            print("-" * 40)
                            print(f"Time taken: {result['time_taken']} seconds")
                            print(f"Tokens generated: {result.get('tokens_generated', 'N/A')}")
                    
                    # Unload model
                    unload_model(model_path)
                    print(f"\nUnloaded model: {model_path}")
            else:
                print("Exiting...")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("No models found. Please download a model first.")