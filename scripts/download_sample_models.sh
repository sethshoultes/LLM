#!/bin/bash
# Script to download sample models of different formats for testing

# Set up directories
BASE_DIR="/Volumes/LLM"
MODELS_DIR="$BASE_DIR/LLM-MODELS"
QUANTIZED_DIR="$MODELS_DIR/quantized"
OPEN_SOURCE_DIR="$MODELS_DIR/open-source"

# Create directories if they don't exist
mkdir -p "$QUANTIZED_DIR/gguf"
mkdir -p "$QUANTIZED_DIR/ggml"
mkdir -p "$QUANTIZED_DIR/awq"
mkdir -p "$OPEN_SOURCE_DIR/mistral/7b"
mkdir -p "$OPEN_SOURCE_DIR/phi/2"
mkdir -p "$OPEN_SOURCE_DIR/llama/7b"

# Define models to download
# Format: URL|output_path|description
MODELS=(
    # TinyLlama GGUF - very small model for testing
    "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf|$QUANTIZED_DIR/gguf/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf|TinyLlama 1.1B Chat GGUF (Q4_K_M)"
    
    # Phi-2 GGUF - small but capable model
    "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf|$QUANTIZED_DIR/gguf/phi-2.Q4_K_M.gguf|Phi-2 GGUF (Q4_K_M)"
    
    # Add more models here as needed
)

# Function to download a model
download_model() {
    local url=$1
    local output_path=$2
    local description=$3
    
    if [ -f "$output_path" ]; then
        echo "✅ $description already exists at $output_path"
    else
        echo "⬇️ Downloading $description..."
        mkdir -p "$(dirname "$output_path")"
        # Use curl to download
        curl -L "$url" -o "$output_path"
        
        if [ $? -eq 0 ]; then
            echo "✅ Successfully downloaded $description"
        else
            echo "❌ Failed to download $description"
        fi
    fi
}

# Main execution
echo "🔄 Downloading sample models for multi-format testing..."

for model_info in "${MODELS[@]}"; do
    IFS='|' read -r url output_path description <<< "$model_info"
    download_model "$url" "$output_path" "$description"
done

echo "✨ Done! Sample models downloaded for testing."
echo "You can now test different model formats using the LLM interface."