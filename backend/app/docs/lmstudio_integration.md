# LMStudio Integration

This document explains how to use the LMStudio provider for local LLM inference in the Reactrine backend.

## Overview

LMStudio is a local LLM inference server that provides an OpenAI-compatible API. This integration allows you to use local models through LMStudio while maintaining the same interface as other LLM providers.

## Configuration

### Environment Variables

Set the following environment variables in your configuration:

```bash
LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://192.168.178.191:1234/v1
LMSTUDIO_MODEL=local-model  # Fallback default, actual model should be set via API
```

**Note:** The `LMSTUDIO_MODEL` environment variable serves as a fallback default. The actual model used should be configured through the `/api/v1/llm-settings` endpoint, which will override this default setting.

### LMStudio Server Setup

1. Download and install LMStudio from [https://lmstudio.ai](https://lmstudio.ai)
2. Load a model in LMStudio
3. Start the local server (usually on port 1234)
4. Verify the server is running by checking: `http://localhost:1234/v1/models`

## Supported Endpoints

The LMStudio integration supports all standard LLM operations:

- **Text Generation**: `get_response(prompt)`
- **Structured Responses**: `get_structured_response(prompt, response_model)`
- **Streaming**: `stream_response(prompt)`
- **Model Discovery**: Available via the `/llm-settings/lmstudio/models` API endpoint

## API Endpoints

### Get Available Models

```http
GET /api/v1/llm-settings/lmstudio/models
Authorization: Bearer <your-token>
```

Returns a list of available models from the LMStudio server:

```json
["llama-3.2-3b-instruct", "mistral-7b-instruct", "codellama-7b"]
```

### Configure LMStudio Provider

```http
PATCH /api/v1/llm-settings
Content-Type: application/json
Authorization: Bearer <your-token>

{
  "provider": "lmstudio",
  "lmstudio_model": "llama-3.2-3b-instruct"
}
```

## Usage Examples

### Basic Text Generation

```python
from app.services.llm import get_llm_service

# Get configured LLM service
llm_service = await get_llm_service()

# Generate response
response = await llm_service.get_response("Explain quantum computing")
print(response)
```

### Model Override

```python
from app.services.llm.factory import get_llm_service_with_overrides

# Use specific LMStudio model
result = await get_llm_service_with_overrides(
    provider="lmstudio",
    model="mistral-7b-instruct"
)

response = await result.service.get_response("Write a Python function")
print(f"Used provider: {result.provider}, model: {result.model}")
```

### Structured Response

```python
from pydantic import BaseModel

class CodeResponse(BaseModel):
    language: str
    code: str
    explanation: str

response = await llm_service.get_structured_response(
    "Write a hello world function in Python",
    CodeResponse
)
```

## Configuration Details

### LMStudioConfig

```python
class LMStudioConfig(BaseModel):
    base_url: str  # LMStudio server URL
    default_model: str  # Default model name
    max_retries: int = 3  # Retry attempts
    timeout: int = 60  # Request timeout in seconds
```

### Database Schema

The `llmsettings` table includes:

```sql
lmstudio_model VARCHAR  -- Selected LMStudio model name
```

## Features

- **OpenAI Compatible**: Uses the same interface as OpenAI for seamless integration
- **Model Discovery**: Automatically fetch available models from LMStudio server
- **Error Handling**: Graceful fallbacks and detailed error messages
- **No API Key Required**: LMStudio runs locally without authentication
- **JSON Mode Support**: Attempts to use structured output, falls back to prompt engineering
- **Streaming Support**: Real-time response streaming

## Network Configuration

### Local Setup

```bash
LMSTUDIO_BASE_URL=http://localhost:1234/v1
```

### Remote Setup

```bash
LMSTUDIO_BASE_URL=http://192.168.178.191:1234/v1
```

### Docker Setup

If running in Docker, ensure the LMStudio server is accessible:

```bash
LMSTUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

## Troubleshooting

### Common Issues

1. **Connection Refused**

   - Ensure LMStudio server is running
   - Check the base URL is correct
   - Verify network connectivity

2. **No Models Available**

   - Load at least one model in LMStudio
   - Restart the LMStudio server
   - Check the models endpoint: `curl http://localhost:1234/v1/models`

3. **Slow Responses**
   - Consider using smaller models
   - Adjust timeout settings
   - Monitor system resources

### Debug Mode

Enable debug logging to see detailed LLM calls:

```python
import logging
logging.getLogger("app.services.llm").setLevel(logging.DEBUG)
```

## Performance Considerations

- **Model Size**: Larger models provide better quality but slower inference
- **Hardware**: GPU acceleration significantly improves performance
- **Concurrent Requests**: LMStudio handles multiple requests but may queue them
- **Memory Usage**: Ensure sufficient RAM for model loading

## Security Notes

- LMStudio runs locally, no data sent to external services
- No API keys required or transmitted
- Suitable for sensitive or private data processing
- Consider network security if running on remote machines
