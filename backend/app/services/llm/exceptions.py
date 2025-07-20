"""Custom exceptions for LLM service operations."""


class LLMGenerationError(Exception):
    """Custom exception for errors during LLM response generation."""


class LLMConfigurationError(Exception):
    """Custom exception for configuration errors."""


class LLMProviderError(Exception):
    """Custom exception for provider-specific errors."""


class LLMRateLimitError(LLMGenerationError):
    """Custom exception for rate limiting errors."""


class LLMValidationError(LLMGenerationError):
    """Custom exception for response validation errors."""
