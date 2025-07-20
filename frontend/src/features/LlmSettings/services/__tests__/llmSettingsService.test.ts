import {
  mockCreateLLMSettings,
  mockGeneratedLLMSettings,
  mockLLMSettings,
  mockLMStudioModels,
} from '@/test/factories';
import { createMockError } from '@/test/utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Mock the generated API client using vi.hoisted to ensure it runs before imports
const mockLlmService = vi.hoisted(() => ({
  getLlmSettingsApiV1LlmSettingsGet: vi.fn(),
  updateLlmSettingsApiV1LlmSettingsPatch: vi.fn(),
  createLlmSettingsApiV1LlmSettingsPost: vi.fn(),
  getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet: vi.fn(),
}));

// Mock the generated client module
vi.mock('@/lib/api-client', () => ({
  LlmService: mockLlmService,
}));

// Import the service functions after mocking
import {
  createSettings,
  fetchLMStudioModels,
  fetchSettings,
  updateSettings,
} from '../llmSettingsService';

describe('LlmSettingsService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('fetchSettings', () => {
    it('should fetch settings from generated client', async () => {
      // Arrange
      const mockResponse = mockGeneratedLLMSettings();
      mockLlmService.getLlmSettingsApiV1LlmSettingsGet.mockResolvedValue(mockResponse);

      // Act
      const result = await fetchSettings();

      // Assert
      expect(mockLlmService.getLlmSettingsApiV1LlmSettingsGet).toHaveBeenCalledTimes(1);
      expect(result).toEqual({
        id: mockResponse.id,
        provider: mockResponse.provider,
        openai_model: mockResponse.openai_model || '',
        openrouter_model: mockResponse.openrouter_model || '',
        bedrock_model: mockResponse.bedrock_model || '',
        lmstudio_model: mockResponse.lmstudio_model || '',
      });
    });

    it('should transform null values to empty strings', async () => {
      // Arrange
      const mockResponse = mockGeneratedLLMSettings({
        provider: 'openrouter',
        openai_model: null,
        openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
        bedrock_model: null,
        lmstudio_model: null,
      });
      mockLlmService.getLlmSettingsApiV1LlmSettingsGet.mockResolvedValue(mockResponse);

      // Act
      const result = await fetchSettings();

      // Assert
      expect(result).toEqual({
        id: mockResponse.id,
        provider: 'openrouter',
        openai_model: '',
        openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
        bedrock_model: '',
        lmstudio_model: '',
      });
    });

    it('should handle 404 (no settings found)', async () => {
      // Arrange
      const error = createMockError(404, 'Not Found');
      mockLlmService.getLlmSettingsApiV1LlmSettingsGet.mockRejectedValue(error);

      // Act & Assert
      await expect(fetchSettings()).rejects.toThrow('Not Found');
      expect(mockLlmService.getLlmSettingsApiV1LlmSettingsGet).toHaveBeenCalledTimes(1);
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const error = createMockError(401, 'Unauthorized');
      mockLlmService.getLlmSettingsApiV1LlmSettingsGet.mockRejectedValue(error);

      // Act & Assert
      await expect(fetchSettings()).rejects.toThrow('Unauthorized');
      expect(mockLlmService.getLlmSettingsApiV1LlmSettingsGet).toHaveBeenCalledTimes(1);
    });

    it('should handle server errors (500)', async () => {
      // Arrange
      const error = createMockError(500, 'Internal Server Error');
      mockLlmService.getLlmSettingsApiV1LlmSettingsGet.mockRejectedValue(error);

      // Act & Assert
      await expect(fetchSettings()).rejects.toThrow('Internal Server Error');
      expect(mockLlmService.getLlmSettingsApiV1LlmSettingsGet).toHaveBeenCalledTimes(1);
    });
  });

  describe('updateSettings', () => {
    it('should update settings with generated client', async () => {
      // Arrange
      const updatePayload = mockLLMSettings({
        provider: 'openrouter',
        openai_model: '',
        openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
        bedrock_model: '',
        lmstudio_model: '',
      });
      const mockResponse = mockGeneratedLLMSettings({
        provider: 'openrouter',
        openai_model: null,
        openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
        bedrock_model: null,
        lmstudio_model: null,
      });
      mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await updateSettings(updatePayload);

      // Assert
      expect(
        mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch
      ).toHaveBeenCalledWith({
        requestBody: {
          provider: 'openrouter',
          openai_model: null,
          openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
          bedrock_model: null,
          lmstudio_model: null,
        },
      });
      expect(result).toEqual({
        id: mockResponse.id,
        provider: 'openrouter',
        openai_model: '',
        openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
        bedrock_model: '',
        lmstudio_model: '',
      });
    });

    it('should transform empty strings to null for generated client', async () => {
      // Arrange
      const updatePayload = {
        provider: 'bedrock',
        openai_model: '',
        openrouter_model: '',
        bedrock_model: 'anthropic.claude-3-haiku-20240307-v1:0',
        lmstudio_model: '',
      };
      const mockResponse = mockGeneratedLLMSettings({
        provider: 'bedrock',
        openai_model: null,
        openrouter_model: null,
        bedrock_model: 'anthropic.claude-3-haiku-20240307-v1:0',
        lmstudio_model: null,
      });
      mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await updateSettings(updatePayload);

      // Assert
      expect(
        mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch
      ).toHaveBeenCalledWith({
        requestBody: {
          provider: 'bedrock',
          openai_model: null,
          openrouter_model: null,
          bedrock_model: 'anthropic.claude-3-haiku-20240307-v1:0',
          lmstudio_model: null,
        },
      });
      expect(result).toEqual({
        id: mockResponse.id,
        provider: 'bedrock',
        openai_model: '',
        openrouter_model: '',
        bedrock_model: 'anthropic.claude-3-haiku-20240307-v1:0',
        lmstudio_model: '',
      });
    });

    it('should handle partial updates correctly', async () => {
      // Arrange
      const partialUpdate = {
        provider: 'lmstudio',
        lmstudio_model: 'llama-3.2-3b-instruct',
      };
      const mockResponse = mockGeneratedLLMSettings({
        provider: 'lmstudio',
        openai_model: null,
        openrouter_model: null,
        bedrock_model: null,
        lmstudio_model: 'llama-3.2-3b-instruct',
      });
      mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await updateSettings(partialUpdate);

      // Assert
      expect(
        mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch
      ).toHaveBeenCalledWith({
        requestBody: {
          provider: 'lmstudio',
          openai_model: null,
          openrouter_model: null,
          bedrock_model: null,
          lmstudio_model: 'llama-3.2-3b-instruct',
        },
      });
      expect(result).toEqual({
        id: mockResponse.id,
        provider: 'lmstudio',
        openai_model: '',
        openrouter_model: '',
        bedrock_model: '',
        lmstudio_model: 'llama-3.2-3b-instruct',
      });
    });

    it('should handle validation errors (422)', async () => {
      // Arrange
      const invalidPayload = {
        provider: 'invalid-provider',
        openai_model: '',
        openrouter_model: '',
        bedrock_model: '',
        lmstudio_model: '',
      };
      const error = createMockError(422, 'Validation Error', {
        detail: 'Invalid provider specified',
      });
      mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch.mockRejectedValue(error);

      // Act & Assert
      await expect(updateSettings(invalidPayload)).rejects.toThrow('Validation Error');
      expect(
        mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch
      ).toHaveBeenCalledWith({
        requestBody: {
          provider: 'invalid-provider',
          openai_model: null,
          openrouter_model: null,
          bedrock_model: null,
          lmstudio_model: null,
        },
      });
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const updatePayload = mockLLMSettings();
      const error = createMockError(401, 'Unauthorized');
      mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch.mockRejectedValue(error);

      // Act & Assert
      await expect(updateSettings(updatePayload)).rejects.toThrow('Unauthorized');
      expect(
        mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle server errors (500)', async () => {
      // Arrange
      const updatePayload = mockLLMSettings();
      const error = createMockError(500, 'Internal Server Error');
      mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch.mockRejectedValue(error);

      // Act & Assert
      await expect(updateSettings(updatePayload)).rejects.toThrow(
        'Internal Server Error'
      );
      expect(
        mockLlmService.updateLlmSettingsApiV1LlmSettingsPatch
      ).toHaveBeenCalledTimes(1);
    });
  });

  describe('createSettings', () => {
    it('should create settings with generated client', async () => {
      // Arrange
      const createPayload = mockCreateLLMSettings({
        provider: 'openai',
        openai_model: 'gpt-4o-mini',
        openrouter_model: '',
        bedrock_model: '',
        lmstudio_model: '',
      });
      const mockResponse = mockGeneratedLLMSettings({
        id: 1,
        provider: 'openai',
        openai_model: 'gpt-4o-mini',
        openrouter_model: null,
        bedrock_model: null,
        lmstudio_model: null,
      });
      mockLlmService.createLlmSettingsApiV1LlmSettingsPost.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await createSettings(createPayload);

      // Assert
      expect(mockLlmService.createLlmSettingsApiV1LlmSettingsPost).toHaveBeenCalledWith(
        {
          requestBody: {
            provider: 'openai',
            openai_model: 'gpt-4o-mini',
            openrouter_model: null,
            bedrock_model: null,
            lmstudio_model: null,
          },
        }
      );
      expect(result).toEqual({
        id: 1,
        provider: 'openai',
        openai_model: 'gpt-4o-mini',
        openrouter_model: '',
        bedrock_model: '',
        lmstudio_model: '',
      });
    });

    it('should validate required fields', async () => {
      // Arrange
      const incompletePayload = {
        provider: 'openai',
        openai_model: '',
        openrouter_model: '',
        bedrock_model: '',
        lmstudio_model: '',
      };
      const error = createMockError(422, 'Validation Error', {
        detail: 'Model is required for OpenAI provider',
      });
      mockLlmService.createLlmSettingsApiV1LlmSettingsPost.mockRejectedValue(error);

      // Act & Assert
      await expect(createSettings(incompletePayload)).rejects.toThrow(
        'Validation Error'
      );
      expect(mockLlmService.createLlmSettingsApiV1LlmSettingsPost).toHaveBeenCalledWith(
        {
          requestBody: {
            provider: 'openai',
            openai_model: null,
            openrouter_model: null,
            bedrock_model: null,
            lmstudio_model: null,
          },
        }
      );
    });

    it('should handle provider-specific model requirements', async () => {
      // Arrange
      const createPayload = mockCreateLLMSettings({
        provider: 'openrouter',
        openai_model: '',
        openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
        bedrock_model: '',
        lmstudio_model: '',
      });
      const mockResponse = mockGeneratedLLMSettings({
        id: 1,
        provider: 'openrouter',
        openai_model: null,
        openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
        bedrock_model: null,
        lmstudio_model: null,
      });
      mockLlmService.createLlmSettingsApiV1LlmSettingsPost.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await createSettings(createPayload);

      // Assert
      expect(mockLlmService.createLlmSettingsApiV1LlmSettingsPost).toHaveBeenCalledWith(
        {
          requestBody: {
            provider: 'openrouter',
            openai_model: null,
            openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
            bedrock_model: null,
            lmstudio_model: null,
          },
        }
      );
      expect(result).toEqual({
        id: 1,
        provider: 'openrouter',
        openai_model: '',
        openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
        bedrock_model: '',
        lmstudio_model: '',
      });
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const createPayload = mockCreateLLMSettings();
      const error = createMockError(401, 'Unauthorized');
      mockLlmService.createLlmSettingsApiV1LlmSettingsPost.mockRejectedValue(error);

      // Act & Assert
      await expect(createSettings(createPayload)).rejects.toThrow('Unauthorized');
      expect(
        mockLlmService.createLlmSettingsApiV1LlmSettingsPost
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle conflicts (409)', async () => {
      // Arrange
      const createPayload = mockCreateLLMSettings();
      const error = createMockError(409, 'Conflict', {
        detail: 'LLM settings already exist for this user',
      });
      mockLlmService.createLlmSettingsApiV1LlmSettingsPost.mockRejectedValue(error);

      // Act & Assert
      await expect(createSettings(createPayload)).rejects.toThrow('Conflict');
      expect(
        mockLlmService.createLlmSettingsApiV1LlmSettingsPost
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle server errors (500)', async () => {
      // Arrange
      const createPayload = mockCreateLLMSettings();
      const error = createMockError(500, 'Internal Server Error');
      mockLlmService.createLlmSettingsApiV1LlmSettingsPost.mockRejectedValue(error);

      // Act & Assert
      await expect(createSettings(createPayload)).rejects.toThrow(
        'Internal Server Error'
      );
      expect(
        mockLlmService.createLlmSettingsApiV1LlmSettingsPost
      ).toHaveBeenCalledTimes(1);
    });
  });

  describe('fetchLMStudioModels', () => {
    it('should fetch available LMStudio models', async () => {
      // Arrange
      const mockModels = mockLMStudioModels();
      mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet.mockResolvedValue(
        mockModels
      );

      // Act
      const result = await fetchLMStudioModels();

      // Assert
      expect(
        mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet
      ).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockModels);
    });

    it('should handle LMStudio server unavailable (503)', async () => {
      // Arrange
      const error = createMockError(503, 'Service Unavailable', {
        detail: 'LMStudio server is not available',
      });
      mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet.mockRejectedValue(
        error
      );

      // Act & Assert
      await expect(fetchLMStudioModels()).rejects.toThrow('Service Unavailable');
      expect(
        mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet
      ).toHaveBeenCalledTimes(1);
    });

    it('should return empty array when no models available', async () => {
      // Arrange
      mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet.mockResolvedValue(
        []
      );

      // Act
      const result = await fetchLMStudioModels();

      // Assert
      expect(
        mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet
      ).toHaveBeenCalledTimes(1);
      expect(result).toEqual([]);
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const error = createMockError(401, 'Unauthorized');
      mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet.mockRejectedValue(
        error
      );

      // Act & Assert
      await expect(fetchLMStudioModels()).rejects.toThrow('Unauthorized');
      expect(
        mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle server errors (500)', async () => {
      // Arrange
      const error = createMockError(500, 'Internal Server Error');
      mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet.mockRejectedValue(
        error
      );

      // Act & Assert
      await expect(fetchLMStudioModels()).rejects.toThrow('Internal Server Error');
      expect(
        mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle timeout errors', async () => {
      // Arrange
      const error = createMockError(408, 'Request Timeout');
      mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet.mockRejectedValue(
        error
      );

      // Act & Assert
      await expect(fetchLMStudioModels()).rejects.toThrow('Request Timeout');
      expect(
        mockLlmService.getLmstudioModelsApiV1LlmSettingsLmstudioModelsGet
      ).toHaveBeenCalledTimes(1);
    });
  });
});
