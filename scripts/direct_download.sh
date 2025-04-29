#!/bin/bash
# direct_download.sh - Directly download a model without needing Hugging Face API

# Set color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BASE_DIR="$( cd "$DIR/.." >/dev/null 2>&1 && pwd )"

# Load environment variables if .env exists
ENV_FILE="$BASE_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}Loading environment variables from $ENV_FILE${NC}"
    source "$ENV_FILE"
fi

# Banner
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}             Direct Model Download Helper                        ${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Set model parameters
MODEL_NAME="TinyLlama 1.1B Chat"
# Use a smaller model for faster testing
MODEL_URL="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
FILENAME="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
USE_AUTH=false

# Add mistral
if [ "$1" == "mistral" ]; then
  MODEL_NAME="Mistral 7B Instruct v0.2"
  MODEL_URL="https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
  FILENAME="mistral-7b-instruct-v0.2.Q4_K_M.gguf"
  USE_AUTH=false
fi

# Model selection based on command line argument
if [ "$1" == "gemma" ]; then
  if [ -z "$HF_TOKEN" ]; then
    echo -e "${RED}Error: HF_TOKEN not set in .env file${NC}"
    echo "Please create a .env file with your Hugging Face token to download Gemma models."
    echo "Example: cp .env.example .env && nano .env"
    exit 1
  fi
  
  MODEL_NAME="Gemma 7B Instruct"
  MODEL_URL="https://huggingface.co/TheBloke/Gemma-7B-it-GGUF/resolve/main/gemma-7b-it.Q4_K_M.gguf"
  FILENAME="gemma-7b-it.Q4_K_M.gguf"
  USE_AUTH=true
elif [ "$1" == "llama3" ]; then
  if [ -z "$HF_TOKEN" ]; then
    echo -e "${RED}Error: HF_TOKEN not set in .env file${NC}"
    echo "Please create a .env file with your Hugging Face token to download Llama 3 models."
    echo "Example: cp .env.example .env && nano .env"
    exit 1
  fi
  
  MODEL_NAME="Llama 3 8B Instruct"
  MODEL_URL="https://huggingface.co/TheBloke/Llama-3-8B-Instruct-GGUF/resolve/main/llama-3-8b-instruct.Q4_K_M.gguf"
  FILENAME="llama-3-8b-instruct.Q4_K_M.gguf"
  USE_AUTH=true
fi

OUTPUT_DIR="$BASE_DIR/LLM-MODELS/quantized/gguf"

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Determine which download tool to use
if command_exists curl; then
    echo -e "${GREEN}Using curl to download model${NC}"
    echo -e "Downloading ${YELLOW}$MODEL_NAME${NC} to ${YELLOW}$OUTPUT_DIR/${FILENAME}${NC}"
    echo -e "This may take several minutes for this 4GB file..."
    echo ""
    
    # Create temporary directory on the LLM volume for downloading
    TEMP_DIR="$BASE_DIR/temp_download"
    mkdir -p "$TEMP_DIR"
    
    # Download to temporary location first
    if [ "$USE_AUTH" == "true" ]; then
        curl -L "$MODEL_URL" -H "Authorization: Bearer $HF_TOKEN" -o "$TEMP_DIR/$FILENAME"
    else
        curl -L "$MODEL_URL" -o "$TEMP_DIR/$FILENAME"
    fi
    
    # Move to final location
    mv "$TEMP_DIR/$FILENAME" "$OUTPUT_DIR/$FILENAME"
    
    # Remove temp directory
    rm -rf "$TEMP_DIR"
    
    echo -e "${GREEN}Download complete!${NC}"
elif command_exists wget; then
    echo -e "${GREEN}Using wget to download model${NC}"
    echo -e "Downloading ${YELLOW}$MODEL_NAME${NC} to ${YELLOW}$OUTPUT_DIR/${FILENAME}${NC}"
    echo -e "This may take several minutes for this 4GB file..."
    echo ""
    
    # Create temporary directory on the LLM volume
    TEMP_DIR="$BASE_DIR/temp_download"
    mkdir -p "$TEMP_DIR"
    
    # Change to temp directory and download
    cd "$TEMP_DIR"
    if [ "$USE_AUTH" == "true" ]; then
        wget --header="Authorization: Bearer $HF_TOKEN" -O "$FILENAME" "$MODEL_URL"
    else
        wget -O "$FILENAME" "$MODEL_URL"
    fi
    
    # Move to final location
    mv "$FILENAME" "$OUTPUT_DIR/$FILENAME"
    
    # Remove temp directory
    rm -rf "$TEMP_DIR"
    
    echo -e "${GREEN}Download complete!${NC}"
else
    echo -e "${RED}Error: Neither curl nor wget is available.${NC}"
    echo "Please install one of these utilities and try again."
    exit 1
fi

echo ""
echo -e "${GREEN}Model downloaded successfully to: ${YELLOW}$OUTPUT_DIR/$FILENAME${NC}"
echo "You can now use this model with the LLM interface."
echo ""
echo "To launch the interface, run:"
echo -e "${YELLOW}./llm.sh${NC} or ${YELLOW}./llm.sh simple${NC}"
echo ""
echo "To download other models, run:"
echo -e "${YELLOW}./scripts/direct_download.sh${NC} - Downloads TinyLlama (default)"
echo -e "${YELLOW}./scripts/direct_download.sh mistral${NC} - Downloads Mistral 7B Instruct v0.2 (public)"
echo -e "${YELLOW}./scripts/direct_download.sh gemma${NC} - Downloads Gemma 7B Instruct (requires HF_TOKEN in .env)"
echo -e "${YELLOW}./scripts/direct_download.sh llama3${NC} - Downloads Llama 3 8B Instruct (requires HF_TOKEN in .env)"
echo ""
echo "For models requiring authentication:"
echo "1. Copy .env.example to .env: ${YELLOW}cp .env.example .env${NC}"
echo "2. Edit the file and add your Hugging Face token: ${YELLOW}nano .env${NC}"