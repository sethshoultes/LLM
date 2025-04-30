# Model Setup Guide

## Installed Models

Your system now has two models available for use:

1. **TinyLlama 1.1B Chat** (~638 MB)
   - Path: `/Volumes/LLM/LLM-MODELS/quantized/gguf/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`
   - Type: GGUF (Q4_K_M quantization)
   - Best for: Quick interactions, testing, low resource usage
   - Context window: 2048 tokens

2. **Phi-2** (~1.7 GB)
   - Path: `/Volumes/LLM/LLM-MODELS/quantized/gguf/phi-2.Q4_K_M.gguf`
   - Type: GGUF (Q4_K_M quantization)
   - Best for: More advanced reasoning, better quality responses
   - Context window: 2048 tokens

## Using Models with RAG

To use these models with RAG (Retrieval-Augmented Generation):

1. Start the interface with RAG enabled:
   ```bash
   ./llm.sh --rag
   ```

2. In the web interface:
   - Select the desired model from the dropdown
   - Navigate to your RAG project
   - Select documents to include as context
   - Ask your questions

3. Smart Context Management:
   - Enabled by default to optimize document usage for each model
   - Can be disabled with `--no-smart-context` flag if needed

## Recommended Parameter Settings

### For TinyLlama:
- Temperature: 0.7
- Max Tokens: 512-1024
- Top P: 0.95
- Frequency Penalty: 0.0-0.3

### For Phi-2:
- Temperature: 0.7
- Max Tokens: 1024
- Top P: 0.9
- Frequency Penalty: 0.0

## Troubleshooting

If you encounter "out of context" errors:
- Reduce the number of documents used as context
- Use shorter prompts
- Use Smart Context Management (on by default)

## Adding More Models

To add more models to your collection:

1. Edit `/Volumes/LLM/scripts/download_sample_models.sh` and add models to the `MODELS` array
2. Run the script: `bash /Volumes/LLM/scripts/download_sample_models.sh`
3. Alternatively, download models from Hugging Face and place them in appropriate directories

## Model Directory Structure

- Quantized GGUF models: `/Volumes/LLM/LLM-MODELS/quantized/gguf/`
- Quantized GGML models: `/Volumes/LLM/LLM-MODELS/quantized/ggml/`
- Full PyTorch models: `/Volumes/LLM/LLM-MODELS/open-source/[family]/[size]/`

## Recommended Additional Models (Not Installed)

For those interested in expanding their model collection:

1. **Mistral 7B Instruct** (~4GB)
   - URL: `https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf`
   - Best for: High-quality instruction following with reasonable size

2. **Gemma 7B Instruct** (~4GB)  
   - URL: `https://huggingface.co/TheBloke/Gemma-7B-it-GGUF/resolve/main/gemma-7b-it.Q4_K_M.gguf`
   - Best for: Google's high-quality instruction model