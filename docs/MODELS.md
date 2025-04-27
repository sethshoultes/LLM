# Portable LLM Environment - Model Guide

## Supported Model Formats

The environment supports multiple model formats with different characteristics:

### GGUF Models (Recommended)

- **Description**: Successor to GGML, optimized for CPU inference
- **File Extension**: `.gguf`
- **Path**: `/Volumes/LLM/LLM-MODELS/quantized/gguf/`
- **Dependencies**: llama-cpp-python
- **Advantages**: Fast, efficient, works on all supported devices
- **Quantization Levels**:
  - `Q4_K_M`: 4-bit quantization, good balance of size vs. quality
  - `Q5_K_M`: 5-bit quantization, better quality but larger
  - `Q8_0`: 8-bit quantization, best quality but significantly larger

### GGML Models (Legacy)

- **Description**: Older quantized format, predates GGUF
- **File Extension**: `.ggml`, `.bin` (with GGML in path)
- **Path**: `/Volumes/LLM/LLM-MODELS/quantized/ggml/`
- **Dependencies**: llama-cpp-python
- **Advantages**: Compatible with older software, widely available
- **Note**: Consider converting to GGUF for better performance

### PyTorch/Safetensors Models

- **Description**: HuggingFace Transformers models
- **File Extension**: `.safetensors`, `.bin`, `.pt`
- **Path**: `/Volumes/LLM/LLM-MODELS/open-source/[family]/[size]/`
- **Dependencies**: transformers, torch
- **Advantages**: Full model capabilities, GPU acceleration (when available)
- **Note**: Requires more RAM than quantized models

## Recommended Models

### For Portable Use (4GB-8GB RAM)

| Model | Format | Size | Description |
|-------|--------|------|-------------|
| TinyLlama 1.1B Chat | GGUF Q4_K_M | ~600MB | Fast assistant for basic conversations |
| Phi-2 | GGUF Q4_K_M | ~1.7GB | Microsoft's compact but capable model |
| StableLM 3B | GGUF Q4_K_M | ~1.8GB | Good general purpose small model |

### For Mac Studio / High Performance (16GB+ RAM)

| Model | Format | Size | Description |
|-------|--------|------|-------------|
| Mistral 7B Instruct | GGUF Q4_K_M | ~4GB | Excellent performance/size ratio |
| LLaMA 2 7B Chat | GGUF Q4_K_M | ~4GB | Meta's capable instruction model |
| Gemma 7B Instruct | GGUF Q4_K_M | ~4GB | Google's instruction-tuned model |
| Mixtral 8x7B Instruct | GGUF Q4_K_M | ~14GB | Powerful mixture-of-experts model |

### For Raspberry Pi (4GB RAM)

| Model | Format | Size | Description |
|-------|--------|------|-------------|
| TinyLlama 1.1B Chat | GGUF Q4_K_M | ~600MB | Best option for limited RAM |
| Phi-2 | GGUF Q2_K | ~900MB | 2-bit quantized for minimal size |

## Model Sources

Recommended sources for downloading models:

1. **The Bloke** ([HuggingFace](https://huggingface.co/TheBloke))
   - Comprehensive collection of quantized models
   - Multiple quantization levels for each model
   
2. **HuggingFace Model Hub** ([huggingface.co](https://huggingface.co/models))
   - Original model sources
   - PyTorch/safetensors versions
   
3. **Recommended Models**
   - TinyLlama: [TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)
   - Mistral: [TheBloke/Mistral-7B-Instruct-v0.2-GGUF](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)
   - LLaMA 2: [TheBloke/Llama-2-7B-Chat-GGUF](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF)
   - Phi-2: [TheBloke/phi-2-GGUF](https://huggingface.co/TheBloke/phi-2-GGUF)

## Model Compatibility Matrix

| Model Format | Model Size | Mac Studio | MacBook Pro | RPi 8GB | RPi 4GB |
|--------------|------------|------------|-------------|---------|---------|
| GGUF Q4_K_M | 1-2B | ✓ | ✓ | ✓ | ✓ |
| GGUF Q4_K_M | 7B | ✓ | ✓ | ✓ | ✗ |
| GGUF Q4_K_M | 13B+ | ✓ | ✓² | ✗ | ✗ |
| GGUF Q5_K_M | 7B | ✓ | ✓ | ✓³ | ✗ |
| PyTorch | 7B | ✓ | ✓² | ✗ | ✗ |

²Requires 16GB+ RAM  
³May run slowly

## Model Parameter Guide

Different models respond differently to parameter settings. Here are general guidelines:

### Temperature

- **Range**: 0.1 - 2.0
- **Default**: 0.7
- **Effect**: Controls randomness in the output
- **When to adjust**:
  - Lower (0.1-0.3) for factual responses, code generation
  - Medium (0.5-0.7) for general conversation
  - Higher (0.8-1.2) for creative, varied responses

### Top P (Nucleus Sampling)

- **Range**: 0.05 - 1.0
- **Default**: 0.95
- **Effect**: Controls diversity by limiting to top percentage of probability mass
- **When to adjust**:
  - Lower (0.5-0.7) for more focused, deterministic responses
  - Higher (0.9-1.0) for more diverse outputs

### Max Tokens

- **Range**: 64 - 4096
- **Default**: 1024
- **Effect**: Maximum response length
- **When to adjust**:
  - Lower (256-512) for quick answers
  - Higher (2048+) for detailed explanations or creative content
  - Note: Higher values use more memory and take longer to generate

### Frequency Penalty

- **Range**: 0.0 - 2.0
- **Default**: 0.0
- **Effect**: Reduces repetition by penalizing frequent tokens
- **When to adjust**:
  - Increase (0.3-0.7) if responses become repetitive
  - Higher values (1.0+) can significantly change the output style

## System Prompt Examples

System prompts set the overall behavior of the model. Here are effective examples:

```
You are a helpful, concise assistant. Provide accurate information and acknowledge when you don't know something.
```

```
You are a programming expert specializing in Python. Provide code examples with explanations. Focus on best practices and efficient solutions.
```

```
You are a creative writing assistant. Help brainstorm ideas, develop characters, and create engaging narratives. Be imaginative and original.
```

```
You are a math tutor helping a high school student. Explain concepts clearly with step-by-step solutions. Use simple language and check your work.
```

## Managing Model Files

### File Naming Convention

When downloading models, maintain a consistent naming pattern for easier identification:

```
[model-name]-[parameter-size]-[variant].[quantization].[format]
```

Example: `mistral-7b-instruct-v0.2.Q4_K_M.gguf`

### Storage Guidelines

- Keep similar model types in their designated directories
- For multiple quantizations of the same model, include the quantization level in the filename
- Consider creating a `favorites` subdirectory for frequently used models

### Space Management

If your drive space is limited:
- Focus on Q4_K_M models for best size/quality balance
- Remove duplicate models with different quantization levels
- Delete older versions when newer ones are available
- Prioritize models you actually use