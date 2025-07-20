import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { JSX, ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// Import types
import type { HaikuResponse } from '@/types/api';

import { mockHaikuRequest, mockHaikuResponse } from '@/test/factories';
import { createMockError } from '@/test/utils';

// Mock the haiku service
vi.mock('@/features/HaikuGenerator/services/haikuService', () => ({
  generateHaiku: vi.fn(),
}));

import { generateHaiku } from '@/features/HaikuGenerator/services/haikuService';
import { useHaikuGenerator } from '../useHaikuGenerator';

describe('useHaikuGenerator Hook', () => {
  let queryClient: QueryClient;
  let wrapper: ({ children }: { children: ReactNode }) => JSX.Element;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: 1, // Allow 1 retry for error testing
          gcTime: 0,
          staleTime: 0,
        },
        mutations: {
          retry: false,
          gcTime: 0,
        },
      },
    });

    wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    vi.clearAllMocks();
  });

  describe('generateHaiku', () => {
    it('should generate haiku with basic request', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({
        topic: 'nature',
      });
      const mockResponse = mockHaikuResponse({
        haiku:
          "Cherry blossoms fall\nGentle breeze carries petals\nSpring's fleeting beauty",
        lines: [
          'Cherry blossoms fall',
          'Gentle breeze carries petals',
          "Spring's fleeting beauty",
        ],
        syllables: [5, 7, 5],
        model_used: 'gpt-4o-mini',
        provider_used: 'openai',
      });
      vi.mocked(generateHaiku).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Assert - initial state
      expect(result.current.isIdle).toBe(true);
      expect(result.current.isPending).toBe(false);
      expect(result.current.data).toBeUndefined();

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.isPending).toBe(false);
      expect(result.current.error).toBeNull();
      expect(generateHaiku).toHaveBeenCalledWith(mockRequest);
      expect(generateHaiku).toHaveBeenCalledTimes(1);
    });

    it('should generate haiku with different topics', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({
        topic: 'technology',
      });
      const mockResponse = mockHaikuResponse({
        haiku: 'Code flows like water\nAlgorithms dance in light\nDigital dreams born',
        lines: [
          'Code flows like water',
          'Algorithms dance in light',
          'Digital dreams born',
        ],
        syllables: [5, 7, 5],
        model_used: 'gpt-4o-mini',
        provider_used: 'openai',
      });
      vi.mocked(generateHaiku).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(generateHaiku).toHaveBeenCalledWith(mockRequest);
    });

    it('should generate haiku with different styles', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({
        topic: 'ocean',
        style: 'melancholic',
      });
      const mockResponse = mockHaikuResponse({
        haiku:
          'Waves crash endlessly\nSalt tears mix with ocean spray\nLoneliness echoes',
        lines: [
          'Waves crash endlessly',
          'Salt tears mix with ocean spray',
          'Loneliness echoes',
        ],
        syllables: [5, 7, 5],
        model_used: 'gpt-4o-mini',
        provider_used: 'openai',
      });
      vi.mocked(generateHaiku).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(generateHaiku).toHaveBeenCalledWith(mockRequest);
    });

    it('should generate haiku with provider overrides', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({
        topic: 'mountains',
        provider: 'openrouter',
      });
      const mockResponse = mockHaikuResponse({
        haiku:
          'Peaks touch the sky high\nSnow-capped giants stand in awe\nSilence speaks volumes',
        lines: [
          'Peaks touch the sky high',
          'Snow-capped giants stand in awe',
          'Silence speaks volumes',
        ],
        syllables: [5, 7, 5],
        model_used: 'anthropic/claude-3-haiku',
        provider_used: 'openrouter',
      });
      vi.mocked(generateHaiku).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.data?.provider_used).toBe('openrouter');
      expect(generateHaiku).toHaveBeenCalledWith(mockRequest);
    });

    it('should generate haiku with model overrides', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({
        topic: 'forest',
        provider: 'openai',
        model: 'gpt-4',
      });
      const mockResponse = mockHaikuResponse({
        haiku:
          'Ancient trees whisper\nSecrets hidden in their bark\nWisdom grows in rings',
        lines: [
          'Ancient trees whisper',
          'Secrets hidden in their bark',
          'Wisdom grows in rings',
        ],
        syllables: [5, 7, 5],
        model_used: 'gpt-4',
        provider_used: 'openai',
      });
      vi.mocked(generateHaiku).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.data?.model_used).toBe('gpt-4');
      expect(generateHaiku).toHaveBeenCalledWith(mockRequest);
    });

    it('should generate haiku with LMStudio provider', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({
        topic: 'rain',
        provider: 'lmstudio',
        model: 'llama-3.2-3b-instruct',
      });
      const mockResponse = mockHaikuResponse({
        haiku:
          'Raindrops kiss the earth\nPetrichor fills the warm air\nLife awakens fresh',
        lines: [
          'Raindrops kiss the earth',
          'Petrichor fills the warm air',
          'Life awakens fresh',
        ],
        syllables: [5, 7, 5],
        model_used: 'llama-3.2-3b-instruct',
        provider_used: 'lmstudio',
      });
      vi.mocked(generateHaiku).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.data?.provider_used).toBe('lmstudio');
      expect(generateHaiku).toHaveBeenCalledWith(mockRequest);
    });

    it('should generate haiku with Bedrock provider', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({
        topic: 'stars',
        provider: 'bedrock',
        model: 'anthropic.claude-3-haiku-20240307-v1:0',
      });
      const mockResponse = mockHaikuResponse({
        haiku:
          'Stars dance in the night\nCosmic ballet of bright light\nUniverse unfolds',
        lines: [
          'Stars dance in the night',
          'Cosmic ballet of bright light',
          'Universe unfolds',
        ],
        syllables: [5, 7, 5],
        model_used: 'anthropic.claude-3-haiku-20240307-v1:0',
        provider_used: 'bedrock',
      });
      vi.mocked(generateHaiku).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.data?.provider_used).toBe('bedrock');
      expect(generateHaiku).toHaveBeenCalledWith(mockRequest);
    });

    it('should handle loading states', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({ topic: 'loading test' });
      let resolvePromise: (value: HaikuResponse) => void;
      const promise = new Promise<HaikuResponse>(resolve => {
        resolvePromise = resolve;
      });
      vi.mocked(generateHaiku).mockReturnValue(promise);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert - should be pending after mutation is triggered
      await waitFor(() => {
        expect(result.current.isPending).toBe(true);
      });
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBeNull();

      // Resolve the promise
      const mockResponse = mockHaikuResponse({
        haiku:
          'Loading test complete\nAsynchronous calls resolve\nState changes tracked well',
        lines: [
          'Loading test complete',
          'Asynchronous calls resolve',
          'State changes tracked well',
        ],
        syllables: [5, 7, 5],
        model_used: 'gpt-4o-mini',
        provider_used: 'openai',
      });
      resolvePromise!(mockResponse);

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });
    });

    it('should handle generation errors', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({ topic: 'error test' });
      const error = createMockError(500, 'Internal Server Error');
      vi.mocked(generateHaiku).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
      expect(result.current.isPending).toBe(false);
    });

    it('should handle timeout errors', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({ topic: 'timeout test' });
      const error = createMockError(408, 'Request Timeout');
      vi.mocked(generateHaiku).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle rate limit errors', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({ topic: 'rate limit test' });
      const error = createMockError(429, 'Too Many Requests');
      vi.mocked(generateHaiku).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle validation errors', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({ topic: '' }); // Empty topic
      const error = createMockError(422, 'Validation Error');
      vi.mocked(generateHaiku).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle authentication errors', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({ topic: 'auth test' });
      const error = createMockError(401, 'Unauthorized');
      vi.mocked(generateHaiku).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle service unavailable errors', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({ topic: 'service test' });
      const error = createMockError(503, 'Service Unavailable');
      vi.mocked(generateHaiku).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle minimal request with topic only', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({
        topic: 'minimal',
        // No style, provider, or model specified
      });
      const mockResponse = mockHaikuResponse({
        haiku: 'Simple beauty shines\nMinimal request fulfilled\nElegance in less',
        lines: [
          'Simple beauty shines',
          'Minimal request fulfilled',
          'Elegance in less',
        ],
        syllables: [5, 7, 5],
        model_used: 'gpt-4o-mini',
        provider_used: 'openai',
      });
      vi.mocked(generateHaiku).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(generateHaiku).toHaveBeenCalledWith(mockRequest);
    });

    it('should handle complex haiku response with metadata', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({
        topic: 'complex',
        style: 'philosophical',
        provider: 'openai',
        model: 'gpt-4',
      });
      const mockResponse = mockHaikuResponse({
        haiku:
          'Thoughts within thoughts dwell\nComplexity breeds wisdom\nSimplicity found',
        lines: [
          'Thoughts within thoughts dwell',
          'Complexity breeds wisdom',
          'Simplicity found',
        ],
        syllables: [5, 7, 5],
        model_used: 'gpt-4',
        provider_used: 'openai',
      });
      vi.mocked(generateHaiku).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.data?.lines).toHaveLength(3);
      expect(result.current.data?.syllables).toEqual([5, 7, 5]);
      expect(result.current.data?.model_used).toBe('gpt-4');
      expect(result.current.data?.provider_used).toBe('openai');
    });

    it('should handle network errors', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({ topic: 'network test' });
      const error = new Error('Network Error');
      vi.mocked(generateHaiku).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle unknown errors', async () => {
      // Arrange
      const mockRequest = mockHaikuRequest({ topic: 'unknown error test' });
      const error = new Error('Unknown error occurred');
      vi.mocked(generateHaiku).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useHaikuGenerator(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });
  });
});
