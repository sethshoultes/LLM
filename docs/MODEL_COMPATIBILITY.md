# Model Compatibility List

This document provides a comprehensive list of language models that have been tested and verified to work with the LLM Platform, along with their performance characteristics, memory requirements, and any specific configuration notes.

## Overview

The LLM Platform supports multiple model formats and architectures, with varying performance characteristics. This guide will help you select the most appropriate model for your use case and hardware.

## Supported Model Formats

- **GGUF**: Recommended format for CPU inference
- **GGML**: Legacy format (still supported)
- **PyTorch/Safetensors**: Full precision models (higher memory requirements)

## Model Families

### LLaMA & LLaMA 2

LLaMA models are general-purpose language models developed by Meta AI.

#### LLaMA 2 7B

| Format | Quantization | RAM Required | Tokens/sec | Suitable For | Notes |
|--------|--------------|--------------|------------|--------------|-------|
| GGUF | Q4_K_M | 4-5 GB | 20-30 | General use, low resource systems | Balanced quality and performance |
| GGUF | Q5_K_M | 5-6 GB | 18-25 | Better accuracy | Higher quality, slightly slower |
| GGUF | Q2_K | 3-4 GB | 25-35 | Fast responses, lower quality | Good for testing, lower accuracy |
| GGML | 4bit | 4-5 GB | 15-25 | Legacy systems | Use GGUF if possible |

**Download**: `./llm.sh download HuggingFace TheBloke/Llama-2-7B-GGUF`

#### LLaMA 2 13B

| Format | Quantization | RAM Required | Tokens/sec | Suitable For | Notes |
|--------|--------------|--------------|------------|--------------|-------|
| GGUF | Q4_K_M | 7-8 GB | 15-20 | General use, mid-range systems | Good balance of quality and speed |
| GGUF | Q5_K_M | 8-10 GB | 13-18 | Higher accuracy | Better quality than 7B models |
| GGUF | Q2_K | 5-6 GB | 18-25 | Fast responses | Lower accuracy |

**Download**: `./llm.sh download HuggingFace TheBloke/Llama-2-13B-GGUF`

#### LLaMA 2 70B

| Format | Quantization | RAM Required | Tokens/sec | Suitable For | Notes |
|--------|--------------|--------------|------------|--------------|-------|
| GGUF | Q4_K_M | 35-40 GB | 5-10 | High accuracy on complex tasks | Requires high-end system |
| GGUF | Q2_K | 20-25 GB | 8-15 | Faster responses with good quality | Better for most systems |

**Download**: `./llm.sh download HuggingFace TheBloke/Llama-2-70B-GGUF`

### Mistral

Mistral models offer strong performance with relatively low resource requirements.

#### Mistral 7B

| Format | Quantization | RAM Required | Tokens/sec | Suitable For | Notes |
|--------|--------------|--------------|------------|--------------|-------|
| GGUF | Q4_K_M | 4-5 GB | 20-30 | General use | Often outperforms LLaMA 2 7B |
| GGUF | Q5_K_M | 5-6 GB | 18-25 | Higher accuracy | Good balance of quality and speed |
| GGUF | Q2_K | 3-4 GB | 25-35 | Fast responses | Good for testing |

**Download**: `./llm.sh download HuggingFace TheBloke/Mistral-7B-v0.1-GGUF`

#### Mistral Instruct 7B

| Format | Quantization | RAM Required | Tokens/sec | Suitable For | Notes |
|--------|--------------|--------------|------------|--------------|-------|
| GGUF | Q4_K_M | 4-5 GB | 20-30 | Chat and instruction following | Optimized for chat |
| GGUF | Q5_K_M | 5-6 GB | 18-25 | Higher accuracy chat | Better quality instruction following |

**Download**: `./llm.sh download HuggingFace TheBloke/Mistral-7B-Instruct-v0.1-GGUF`

### Mixtral

Mixtral models use a mixture-of-experts architecture for powerful performance.

#### Mixtral 8x7B

| Format | Quantization | RAM Required | Tokens/sec | Suitable For | Notes |
|--------|--------------|--------------|------------|--------------|-------|
| GGUF | Q4_K_M | 25-30 GB | 8-12 | High accuracy | Comparable to 70B models |
| GGUF | Q2_K | 15-20 GB | 12-18 | Faster responses | Good balance of speed and quality |

**Download**: `./llm.sh download HuggingFace TheBloke/Mixtral-8x7B-v0.1-GGUF`

### Phi

Microsoft Phi models are small but powerful, optimized for efficiency.

#### Phi-2

| Format | Quantization | RAM Required | Tokens/sec | Suitable For | Notes |
|--------|--------------|--------------|------------|--------------|-------|
| GGUF | Q4_K_M | 2-3 GB | 25-35 | Low resource systems | Impressive quality for size |
| GGUF | Q5_K_M | 3-4 GB | 23-30 | Better accuracy | Good for laptops |

**Download**: `./llm.sh download HuggingFace TheBloke/phi-2-GGUF`

### TinyLlama (Sample Model)

| Format | Quantization | RAM Required | Tokens/sec | Suitable For | Notes |
|--------|--------------|--------------|------------|--------------|-------|
| GGUF | Q4_K_M | 1-2 GB | 30-40 | Testing, very low resources | Downloaded by `samples` command |
| GGUF | Q2_K | <1 GB | 35-45 | Minimal systems | Lowest quality but very fast |

**Download**: `./llm.sh samples`

## Embedding Models

The following embedding models are supported for semantic search and RAG features:

### all-MiniLM-L6-v2

| RAM Required | Dimensions | Suitable For | Notes |
|--------------|------------|--------------|-------|
| 100-200 MB | 384 | General semantic search | Good performance/size ratio |

**Download**: Automatically downloaded when RAG is enabled

### all-mpnet-base-v2

| RAM Required | Dimensions | Suitable For | Notes |
|--------------|------------|--------------|-------|
| 400-500 MB | 768 | Higher accuracy search | Better quality but slower |

**Download**: `pip install -e ".[mpnet]"` in the rag/ directory

## Model Parameter Suggestions

Different models perform best with different parameter settings. Here are some general guidelines:

### LLaMA 2 Models

- **Temperature**: 0.7-0.8 works well for most cases
- **Top P**: 0.9 is a good default
- **Repetition Penalty**: 1.1-1.2 helps prevent loops

### Mistral Models

- **Temperature**: 0.5-0.7 for instruct versions
- **Top P**: 0.9-0.95 
- **Repetition Penalty**: 1.0-1.1 (less prone to repetition)

### Mixtral Models

- **Temperature**: 0.7-0.8
- **Top P**: 0.9-0.95
- **Repetition Penalty**: 1.1-1.2

### Phi Models

- **Temperature**: 0.5-0.6
- **Top P**: 0.9
- **Repetition Penalty**: 1.1-1.3 (may need higher values)

## System Prompts

Different models respond best to different system prompts:

### LLaMA 2 Chat Models

```
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question is not clear or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.
```

### Mistral Instruct Models

```
<s>[INST] You are Mistral AI's assistant. You are respectful, direct, and concise. [/INST]</s>
```

### Mixtral Instruct Models

```
<s>[INST] You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. [/INST]</s>
```

### Phi Models

```
You are a helpful AI assistant. Be concise but informative in your responses.
```

## Custom Model Integration

### Adding Your Own Models

1. Place the model file in the appropriate directory:
   - GGUF/GGML models: `LLM-MODELS/quantized/gguf/` or `LLM-MODELS/quantized/ggml/`
   - PyTorch models: `LLM-MODELS/open-source/{family}/{size}/`

2. If using a custom model type, you may need to edit the model registry configuration.

### Testing Model Compatibility

Use the test command to check if a model loads correctly:

```bash
./llm.sh test /path/to/model/file
```

This will attempt to load the model and run a small inference test.

## Troubleshooting Model Issues

### Common Problems and Solutions

#### Model Loads But Generates Garbage Text

- Try a different quantization level (Q4_K_M or Q5_K_M usually work best)
- Verify the model file isn't corrupted (re-download if necessary)
- Some models require specific prompting formats (check model card)

#### Out of Memory Errors

- Try a smaller model size (7B instead of 13B)
- Try a more aggressive quantization (Q2_K uses less memory)
- Close other applications to free up RAM
- Add more swap space (though this will reduce performance)

#### Very Slow Generation

- Use a more quantized version (Q2_K is fastest)
- Reduce the context length if possible
- Try a smaller model variant
- Check CPU usage (other processes may be competing for resources)

#### Model Not Recognized

- Make sure the model format is supported (GGUF/GGML)
- Check file permissions
- Verify the file path is correct
- Try moving the model to the standard directory structure

## Performance Optimization

### CPU Optimization

- Set the number of threads appropriately:
  ```bash
  export OMP_NUM_THREADS=4  # Adjust based on your CPU
  ```

- Enable AVX2/AVX512 if your CPU supports it:
  ```bash
  # Check if your CPU supports these instructions
  grep -q 'avx2' /proc/cpuinfo && echo "AVX2 Supported"
  grep -q 'avx512' /proc/cpuinfo && echo "AVX512 Supported"
  ```

### Memory Management

- If running multiple models in sequence, explicitly unload each model after use
- Adjust the context size to balance between performance and memory usage
- Use batch processing for multiple inferences when possible

## Model Sources

Models can be downloaded from various sources:

- [HuggingFace](https://huggingface.co/models)
- [TheBloke](https://huggingface.co/TheBloke) - Extensive collection of quantized models
- [Anthropic](https://www.anthropic.com/research) - For research models
- [Databricks](https://huggingface.co/databricks) - For Dolly and other open models
- [TII UAE](https://huggingface.co/tiiuae) - For Falcon models

## Legal Considerations

Always check the license terms of models before use. Some models:

- **Llama 2** - Requires accepting Meta's license agreement
- **Mistral** - Available under Apache 2.0 license
- **Phi-2** - Research access only, requires Microsoft agreement
- **MPT** - Available under Apache 2.0 license
- **Falcon** - Available under Apache 2.0 license

Models may have specific usage restrictions even if they're freely downloadable.

## Updates and Versioning

This compatibility list is current as of April 30, 2025. As new models and formats become available, this document will be updated. Check for the latest version before making decisions based on this information.