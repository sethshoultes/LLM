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
    curl -L "$MODEL_URL" -o "$TEMP_DIR/$FILENAME"
    
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
    wget -O "$FILENAME" "$MODEL_URL"
    
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