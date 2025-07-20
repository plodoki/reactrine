import { mockGeneratedHaikuResponse, mockHaikuRequest } from '@/test/factories';
import { createMockError } from '@/test/utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// Mock the generated API client using vi.hoisted to ensure it runs before imports
const mockHaikuService = vi.hoisted(() => ({
  generateHaikuEndpointApiV1HaikuPost: vi.fn(),
}));

// Mock the generated client module
vi.mock('@/lib/api-client', () => ({
  HaikuService: mockHaikuService,
  OpenAPI: {
    BASE: 'http://127.0.0.1:8000',
    WITH_CREDENTIALS: true,
    CREDENTIALS: 'include',
    HEADERS: vi.fn().mockResolvedValue({}),
  },
}));

// Import the service functions after mocking
import { generateHaiku } from '../haikuService';

describe('HaikuService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('generateHaiku', () => {
    it('should generate haiku with generated client', async () => {
      // Arrange
      const request = mockHaikuRequest();
      const mockResponse = mockGeneratedHaikuResponse();
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await generateHaiku(request);

      // Assert
      expect(mockHaikuService.generateHaikuEndpointApiV1HaikuPost).toHaveBeenCalledWith(
        {
          requestBody: request,
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle different haiku themes', async () => {
      // Arrange
      const request = mockHaikuRequest({
        topic: 'technology',
        style: 'modern',
      });
      const mockResponse = mockGeneratedHaikuResponse({
        haiku: 'Code flows like water\nBinary streams of logic\nDigital zen found',
        lines: [
          'Code flows like water',
          'Binary streams of logic',
          'Digital zen found',
        ],
        syllables: [5, 7, 5],
        model_used: 'gpt-4o-mini',
        provider_used: 'openai',
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await generateHaiku(request);

      // Assert
      expect(mockHaikuService.generateHaikuEndpointApiV1HaikuPost).toHaveBeenCalledWith(
        {
          requestBody: {
            topic: 'technology',
            style: 'modern',
            provider: null,
            model: null,
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle provider overrides', async () => {
      // Arrange
      const request = mockHaikuRequest({
        topic: 'ocean',
        provider: 'openrouter',
      });
      const mockResponse = mockGeneratedHaikuResponse({
        haiku:
          'Waves crash on the shore\nEndless blue horizon calls\nOcean whispers peace',
        lines: [
          'Waves crash on the shore',
          'Endless blue horizon calls',
          'Ocean whispers peace',
        ],
        syllables: [5, 7, 5],
        model_used: 'meta-llama/llama-3.2-3b-instruct',
        provider_used: 'openrouter',
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await generateHaiku(request);

      // Assert
      expect(mockHaikuService.generateHaikuEndpointApiV1HaikuPost).toHaveBeenCalledWith(
        {
          requestBody: {
            topic: 'ocean',
            style: 'traditional',
            provider: 'openrouter',
            model: null,
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle model overrides', async () => {
      // Arrange
      const request = mockHaikuRequest({
        topic: 'mountains',
        provider: 'bedrock',
        model: 'anthropic.claude-3-haiku-20240307-v1:0',
      });
      const mockResponse = mockGeneratedHaikuResponse({
        haiku:
          'Peaks touch the sky high\nMajestic silence echoes\nStone guardians stand',
        lines: [
          'Peaks touch the sky high',
          'Majestic silence echoes',
          'Stone guardians stand',
        ],
        syllables: [5, 7, 5],
        model_used: 'anthropic.claude-3-haiku-20240307-v1:0',
        provider_used: 'bedrock',
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await generateHaiku(request);

      // Assert
      expect(mockHaikuService.generateHaikuEndpointApiV1HaikuPost).toHaveBeenCalledWith(
        {
          requestBody: {
            topic: 'mountains',
            style: 'traditional',
            provider: 'bedrock',
            model: 'anthropic.claude-3-haiku-20240307-v1:0',
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle LMStudio provider', async () => {
      // Arrange
      const request = mockHaikuRequest({
        topic: 'winter',
        provider: 'lmstudio',
        model: 'llama-3.2-3b-instruct',
      });
      const mockResponse = mockGeneratedHaikuResponse({
        haiku:
          'Snowflakes dance and fall\nSilent world in white blanket\nWinter dreams unfold',
        lines: [
          'Snowflakes dance and fall',
          'Silent world in white blanket',
          'Winter dreams unfold',
        ],
        syllables: [5, 7, 5],
        model_used: 'llama-3.2-3b-instruct',
        provider_used: 'lmstudio',
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await generateHaiku(request);

      // Assert
      expect(mockHaikuService.generateHaikuEndpointApiV1HaikuPost).toHaveBeenCalledWith(
        {
          requestBody: {
            topic: 'winter',
            style: 'traditional',
            provider: 'lmstudio',
            model: 'llama-3.2-3b-instruct',
          },
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle minimal request (topic only)', async () => {
      // Arrange
      const request = {
        topic: 'love',
      };
      const mockResponse = mockGeneratedHaikuResponse({
        haiku:
          'Hearts beat as one song\nTender moments shared in time\nLove eternal blooms',
        lines: [
          'Hearts beat as one song',
          'Tender moments shared in time',
          'Love eternal blooms',
        ],
        syllables: [5, 7, 5],
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await generateHaiku(request);

      // Assert
      expect(mockHaikuService.generateHaikuEndpointApiV1HaikuPost).toHaveBeenCalledWith(
        {
          requestBody: request,
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle LLM generation failures', async () => {
      // Arrange
      const request = mockHaikuRequest();
      const error = createMockError(422, 'Validation Error', {
        detail: 'Invalid topic provided',
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockRejectedValue(error);

      // Act & Assert
      await expect(generateHaiku(request)).rejects.toThrow(
        'Failed to generate haiku: Validation Error'
      );
      expect(mockHaikuService.generateHaikuEndpointApiV1HaikuPost).toHaveBeenCalledWith(
        {
          requestBody: request,
        }
      );
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const request = mockHaikuRequest();
      const error = createMockError(401, 'Unauthorized');
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockRejectedValue(error);

      // Act & Assert
      await expect(generateHaiku(request)).rejects.toThrow(
        'Failed to generate haiku: Unauthorized'
      );
      expect(
        mockHaikuService.generateHaikuEndpointApiV1HaikuPost
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle provider configuration errors (400)', async () => {
      // Arrange
      const request = mockHaikuRequest({
        provider: 'openai',
        model: 'invalid-model',
      });
      const error = createMockError(400, 'Bad Request', {
        detail: 'Invalid model specified for provider',
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockRejectedValue(error);

      // Act & Assert
      await expect(generateHaiku(request)).rejects.toThrow(
        'Failed to generate haiku: Bad Request'
      );
      expect(mockHaikuService.generateHaikuEndpointApiV1HaikuPost).toHaveBeenCalledWith(
        {
          requestBody: request,
        }
      );
    });

    it('should handle LLM service unavailable (503)', async () => {
      // Arrange
      const request = mockHaikuRequest({
        provider: 'lmstudio',
      });
      const error = createMockError(503, 'Service Unavailable', {
        detail: 'LMStudio server is not available',
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockRejectedValue(error);

      // Act & Assert
      await expect(generateHaiku(request)).rejects.toThrow(
        'Failed to generate haiku: Service Unavailable'
      );
      expect(
        mockHaikuService.generateHaikuEndpointApiV1HaikuPost
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle timeout errors', async () => {
      // Arrange
      const request = mockHaikuRequest();
      const error = createMockError(408, 'Request Timeout');
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockRejectedValue(error);

      // Act & Assert
      await expect(generateHaiku(request)).rejects.toThrow(
        'Failed to generate haiku: Request Timeout'
      );
      expect(
        mockHaikuService.generateHaikuEndpointApiV1HaikuPost
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle server errors (500)', async () => {
      // Arrange
      const request = mockHaikuRequest();
      const error = createMockError(500, 'Internal Server Error');
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockRejectedValue(error);

      // Act & Assert
      await expect(generateHaiku(request)).rejects.toThrow(
        'Failed to generate haiku: Internal Server Error'
      );
      expect(
        mockHaikuService.generateHaikuEndpointApiV1HaikuPost
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle rate limiting errors (429)', async () => {
      // Arrange
      const request = mockHaikuRequest();
      const error = createMockError(429, 'Too Many Requests', {
        detail: 'Rate limit exceeded',
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockRejectedValue(error);

      // Act & Assert
      await expect(generateHaiku(request)).rejects.toThrow(
        'Failed to generate haiku: Too Many Requests'
      );
      expect(
        mockHaikuService.generateHaikuEndpointApiV1HaikuPost
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle network errors', async () => {
      // Arrange
      const request = mockHaikuRequest();
      const networkError = new Error('Network error');
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockRejectedValue(
        networkError
      );

      // Act & Assert
      await expect(generateHaiku(request)).rejects.toThrow(
        'Failed to generate haiku: Network error'
      );
      expect(
        mockHaikuService.generateHaikuEndpointApiV1HaikuPost
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle unknown errors', async () => {
      // Arrange
      const request = mockHaikuRequest();
      const unknownError = 'Unknown error';
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockRejectedValue(
        unknownError
      );

      // Act & Assert
      await expect(generateHaiku(request)).rejects.toThrow(
        'Failed to generate haiku: Unknown error occurred'
      );
      expect(
        mockHaikuService.generateHaikuEndpointApiV1HaikuPost
      ).toHaveBeenCalledTimes(1);
    });

    it('should handle empty topic gracefully', async () => {
      // Arrange
      const request = mockHaikuRequest({
        topic: '',
      });
      const error = createMockError(422, 'Validation Error', {
        detail: 'Topic cannot be empty',
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockRejectedValue(error);

      // Act & Assert
      await expect(generateHaiku(request)).rejects.toThrow(
        'Failed to generate haiku: Validation Error'
      );
      expect(mockHaikuService.generateHaikuEndpointApiV1HaikuPost).toHaveBeenCalledWith(
        {
          requestBody: {
            topic: '',
            style: 'traditional',
            provider: null,
            model: null,
          },
        }
      );
    });

    it('should handle complex haiku response structure', async () => {
      // Arrange
      const request = mockHaikuRequest({
        topic: 'seasons',
        style: 'free verse',
      });
      const mockResponse = mockGeneratedHaikuResponse({
        haiku:
          'Spring rain falls gently\nSummer sun warms the earth\nAutumn leaves dance free\nWinter snow blankets all',
        lines: [
          'Spring rain falls gently',
          'Summer sun warms the earth',
          'Autumn leaves dance free',
          'Winter snow blankets all',
        ],
        syllables: [5, 7, 5, 7],
        model_used: 'gpt-4o-mini',
        provider_used: 'openai',
      });
      mockHaikuService.generateHaikuEndpointApiV1HaikuPost.mockResolvedValue(
        mockResponse
      );

      // Act
      const result = await generateHaiku(request);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(result.lines).toHaveLength(4);
      expect(result.syllables).toHaveLength(4);
    });
  });
});
