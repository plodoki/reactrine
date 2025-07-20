# LLM Provider and Model Overrides

This document explains how to use the enhanced LLM service functionality that allows overriding the default provider and model settings on a per-request basis.

## Overview

The haiku generation endpoint now supports optional `provider` and `model` parameters that allow you to override the default LLM settings configured in the system. This enables testing different models and providers without changing the global configuration.

## Usage

### Basic Request (Uses Default Settings)

```json
{
  "topic": "nature",
  "style": "traditional"
}
```

This will use the current default provider and model configured in the LLM settings.

### Provider Override

```json
{
  "topic": "nature",
  "style": "traditional",
  "provider": "openrouter"
}
```

This will use OpenRouter with its default model, regardless of the system default.

### Model Override

```json
{
  "topic": "nature",
  "style": "traditional",
  "model": "gpt-4o"
}
```

This will use the specified model with the current default provider.

### Both Provider and Model Override

```json
{
  "topic": "nature",
  "style": "traditional",
  "provider": "openrouter",
  "model": "anthropic/claude-3-5-sonnet"
}
```

This will use the specified provider and model combination.

## Supported Providers

- `openai` - OpenAI models (gpt-4, gpt-4o-mini, etc.)
- `openrouter` - OpenRouter proxy service (supports many models)
- `bedrock` - Amazon Bedrock (Claude, etc.)

## Response Changes

The response now includes information about which provider and model were actually used:

```json
{
  "haiku": "Cherry blossoms fall\nGently on the morning dew\nSpring's gentle whisper",
  "lines": [
    "Cherry blossoms fall",
    "Gently on the morning dew",
    "Spring's gentle whisper"
  ],
  "syllables": [5, 7, 5],
  "model_used": "gpt-4o",
  "provider_used": "openai"
}
```

## Implementation Details

### Service Architecture

The enhancement adds a new function `get_llm_service_with_overrides()` that returns a structured `LLMServiceResult` dataclass containing the service instance, provider, and model information for better type safety and clarity.

### Backward Compatibility

The changes are fully backward compatible:

- Existing requests without provider/model parameters work exactly as before
- The original `get_llm_service()` function remains unchanged
- All existing API contracts are preserved

### Error Handling

- Invalid provider names return appropriate error messages
- Missing configuration (e.g., API keys) for overridden providers will fail gracefully
- Model validation is handled by the underlying LLM provider

## Benefits

1. **Testing**: Easily test different models and providers without changing global settings
2. **Flexibility**: Use different models for different types of content
3. **Experimentation**: Compare outputs from different providers/models
4. **Performance**: Use faster/cheaper models for specific use cases
5. **Quality**: Use higher-quality models when needed

## Future Extensions

This pattern can be extended to other services that use LLMs:

- Text summarization with provider/model selection
- Translation services with model preferences
- Content generation with quality/speed trade-offs
