import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { JSX, ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// Import types
import type { LLMSettings } from '@/types/api';

import {
  mockCreateLLMSettings,
  mockLLMSettings,
  mockLMStudioModels,
} from '@/test/factories';
import { createMockError } from '@/test/utils';

// Mock the LLM settings service
vi.mock('@/features/LlmSettings/services/llmSettingsService', () => ({
  fetchSettings: vi.fn(),
  updateSettings: vi.fn(),
  createSettings: vi.fn(),
  fetchLMStudioModels: vi.fn(),
}));

// Mock the notifications hook
const mockShowSuccessNotification = vi.fn();
const mockShowErrorNotification = vi.fn();

vi.mock('@/hooks/useNotifications', () => ({
  useNotifications: () => ({
    showSuccessNotification: mockShowSuccessNotification,
    showErrorNotification: mockShowErrorNotification,
  }),
}));

import {
  createSettings,
  fetchLMStudioModels,
  fetchSettings,
  updateSettings,
} from '@/features/LlmSettings/services/llmSettingsService';
import {
  useCreateLlmSettings,
  useLMStudioModels,
  useLlmSettings,
  useUpdateLlmSettings,
} from '../useLlmSettings';

describe('useLlmSettings Hooks', () => {
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

  describe('useLlmSettings', () => {
    it('should fetch LLM settings successfully', async () => {
      // Arrange
      const mockSettings = mockLLMSettings({
        provider: 'openai',
        openai_model: 'gpt-4o-mini',
      });
      vi.mocked(fetchSettings).mockResolvedValue(mockSettings);

      // Act
      const { result } = renderHook(() => useLlmSettings(), { wrapper });

      // Assert
      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockSettings);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(fetchSettings).toHaveBeenCalledTimes(1);
    });

    it('should handle loading state correctly', async () => {
      // Arrange
      let resolvePromise: (value: LLMSettings) => void;
      const promise = new Promise<LLMSettings>(resolve => {
        resolvePromise = resolve;
      });
      vi.mocked(fetchSettings).mockReturnValue(promise);

      // Act
      const { result } = renderHook(() => useLlmSettings(), { wrapper });

      // Assert - should be loading initially
      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBeNull();

      // Resolve the promise
      resolvePromise!(mockLLMSettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('should handle error state correctly', async () => {
      // Arrange
      const error = createMockError(500, 'Internal Server Error');
      vi.mocked(fetchSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useLlmSettings(), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const error = createMockError(401, 'Unauthorized');
      vi.mocked(fetchSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useLlmSettings(), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle not found errors (404)', async () => {
      // Arrange
      const error = createMockError(404, 'Settings not found');
      vi.mocked(fetchSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useLlmSettings(), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
    });

    it('should retry only once on failure', async () => {
      // Arrange
      const error = createMockError(500, 'Server Error');
      vi.mocked(fetchSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useLlmSettings(), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      // Should have been called twice (initial + 1 retry)
      expect(fetchSettings).toHaveBeenCalledTimes(2);
    });
  });

  describe('useUpdateLlmSettings', () => {
    it('should update LLM settings successfully', async () => {
      // Arrange
      const originalSettings = mockLLMSettings({
        provider: 'openai',
        openai_model: 'gpt-4o-mini',
      });
      const updatedSettings = mockLLMSettings({
        provider: 'openrouter',
        openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
      });

      // Pre-populate the cache
      queryClient.setQueryData(['llm-settings'], originalSettings);

      vi.mocked(updateSettings).mockResolvedValue(updatedSettings);

      // Act
      const { result } = renderHook(() => useUpdateLlmSettings(), { wrapper });

      // Assert
      expect(result.current.isPending).toBe(false);

      // Trigger the mutation
      result.current.mutate(updatedSettings);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(updatedSettings);
      expect(result.current.isPending).toBe(false);
      expect(updateSettings).toHaveBeenCalledWith(updatedSettings);
      expect(updateSettings).toHaveBeenCalledTimes(1);

      // Note: Cache update is handled by the onSuccess callback
      // and tested implicitly through the mutation success
    });

    it('should handle partial updates correctly', async () => {
      // Arrange
      const originalSettings = mockLLMSettings({
        provider: 'openai',
        openai_model: 'gpt-4o-mini',
      });
      const partialUpdate = {
        provider: 'bedrock',
        bedrock_model: 'anthropic.claude-3-haiku-20240307-v1:0',
      };
      const updatedSettings = mockLLMSettings({
        ...originalSettings,
        ...partialUpdate,
      });

      queryClient.setQueryData(['llm-settings'], originalSettings);
      vi.mocked(updateSettings).mockResolvedValue(updatedSettings);

      // Act
      const { result } = renderHook(() => useUpdateLlmSettings(), { wrapper });
      result.current.mutate(partialUpdate);

      // Assert
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(updateSettings).toHaveBeenCalledWith(partialUpdate);
      expect(result.current.data).toEqual(updatedSettings);
    });

    it('should handle validation errors (422)', async () => {
      // Arrange
      const error = createMockError(422, 'Validation Error');
      vi.mocked(updateSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useUpdateLlmSettings(), { wrapper });
      result.current.mutate(mockLLMSettings());

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.isPending).toBe(false);
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const error = createMockError(401, 'Unauthorized');
      vi.mocked(updateSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useUpdateLlmSettings(), { wrapper });
      result.current.mutate(mockLLMSettings());

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
    });

    it('should handle server errors (500)', async () => {
      // Arrange
      const error = createMockError(500, 'Internal Server Error');
      vi.mocked(updateSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useUpdateLlmSettings(), { wrapper });
      result.current.mutate(mockLLMSettings());

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
    });

    it('should invalidate queries on error', async () => {
      // Arrange
      const originalSettings = mockLLMSettings();
      queryClient.setQueryData(['llm-settings'], originalSettings);

      const error = createMockError(500, 'Update failed');
      vi.mocked(updateSettings).mockRejectedValue(error);

      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

      // Act
      const { result } = renderHook(() => useUpdateLlmSettings(), { wrapper });
      result.current.mutate(mockLLMSettings());

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: ['llm-settings'],
      });
    });
  });

  describe('useCreateLlmSettings', () => {
    it('should create LLM settings successfully', async () => {
      // Arrange
      const newSettings = mockCreateLLMSettings({
        provider: 'openai',
        openai_model: 'gpt-4o-mini',
      });
      const createdSettings = mockLLMSettings({
        id: 1,
        ...newSettings,
      });

      vi.mocked(createSettings).mockResolvedValue(createdSettings);

      // Act
      const { result } = renderHook(() => useCreateLlmSettings(), { wrapper });

      // Assert
      expect(result.current.isPending).toBe(false);

      // Trigger the mutation
      result.current.mutate(newSettings);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(createdSettings);
      expect(result.current.isPending).toBe(false);
      expect(createSettings).toHaveBeenCalledWith(newSettings);
      expect(createSettings).toHaveBeenCalledTimes(1);

      // Note: Cache update is handled by the onSuccess callback
      // and tested implicitly through the mutation success
    });

    it('should handle different provider types', async () => {
      // Arrange
      const openRouterSettings = mockCreateLLMSettings({
        provider: 'openrouter',
        openrouter_model: 'meta-llama/llama-3.2-3b-instruct',
      });
      const createdSettings = mockLLMSettings({
        id: 1,
        ...openRouterSettings,
      });

      vi.mocked(createSettings).mockResolvedValue(createdSettings);

      // Act
      const { result } = renderHook(() => useCreateLlmSettings(), { wrapper });
      result.current.mutate(openRouterSettings);

      // Assert
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(createSettings).toHaveBeenCalledWith(openRouterSettings);
      expect(result.current.data).toEqual(createdSettings);
    });

    it('should handle validation errors (422)', async () => {
      // Arrange
      const error = createMockError(422, 'Validation Error');
      vi.mocked(createSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useCreateLlmSettings(), { wrapper });
      result.current.mutate(mockCreateLLMSettings());

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.isPending).toBe(false);
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const error = createMockError(401, 'Unauthorized');
      vi.mocked(createSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useCreateLlmSettings(), { wrapper });
      result.current.mutate(mockCreateLLMSettings());

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
    });

    it('should handle conflict errors (409)', async () => {
      // Arrange
      const error = createMockError(409, 'Settings already exist');
      vi.mocked(createSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useCreateLlmSettings(), { wrapper });
      result.current.mutate(mockCreateLLMSettings());

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
    });

    it('should handle server errors (500)', async () => {
      // Arrange
      const error = createMockError(500, 'Internal Server Error');
      vi.mocked(createSettings).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useCreateLlmSettings(), { wrapper });
      result.current.mutate(mockCreateLLMSettings());

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
    });

    it('should invalidate queries on error', async () => {
      // Arrange
      const error = createMockError(500, 'Creation failed');
      vi.mocked(createSettings).mockRejectedValue(error);

      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

      // Act
      const { result } = renderHook(() => useCreateLlmSettings(), { wrapper });
      result.current.mutate(mockCreateLLMSettings());

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(invalidateQueriesSpy).toHaveBeenCalledWith({
        queryKey: ['llm-settings'],
      });
    });
  });

  describe('useLMStudioModels', () => {
    it('should fetch LMStudio models successfully when enabled', async () => {
      // Arrange
      const mockModels = mockLMStudioModels();
      vi.mocked(fetchLMStudioModels).mockResolvedValue(mockModels);

      // Act
      const { result } = renderHook(() => useLMStudioModels(), { wrapper });

      // Assert - should not be loading initially (enabled: false)
      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toBeUndefined();

      // Enable the query
      result.current.refetch();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockModels);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(fetchLMStudioModels).toHaveBeenCalledTimes(1);
    });

    it('should handle empty models list', async () => {
      // Arrange
      vi.mocked(fetchLMStudioModels).mockResolvedValue([]);

      // Act
      const { result } = renderHook(() => useLMStudioModels(), { wrapper });
      result.current.refetch();

      // Assert
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual([]);
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle LMStudio server unavailable (503)', async () => {
      // Arrange
      const error = createMockError(503, 'LMStudio server unavailable');
      vi.mocked(fetchLMStudioModels).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useLMStudioModels(), { wrapper });
      result.current.refetch();

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle timeout errors (408)', async () => {
      // Arrange
      const error = createMockError(408, 'Request timeout');
      vi.mocked(fetchLMStudioModels).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useLMStudioModels(), { wrapper });
      result.current.refetch();

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
    });

    it('should handle network errors', async () => {
      // Arrange
      const error = createMockError(500, 'Network error');
      vi.mocked(fetchLMStudioModels).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useLMStudioModels(), { wrapper });
      result.current.refetch();

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
    });

    it('should retry only once on failure', async () => {
      // Arrange
      const error = createMockError(500, 'Server Error');
      vi.mocked(fetchLMStudioModels).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useLMStudioModels(), { wrapper });
      result.current.refetch();

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      // Should have been called twice (initial + 1 retry)
      expect(fetchLMStudioModels).toHaveBeenCalledTimes(2);
    });

    it('should respect stale time of 5 minutes', async () => {
      // Arrange
      const mockModels = mockLMStudioModels();
      vi.mocked(fetchLMStudioModels).mockResolvedValue(mockModels);

      // Create a new query client with stale time enabled for this test
      const staleTimeQueryClient = new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            gcTime: 0,
            staleTime: 5 * 60 * 1000, // 5 minutes
          },
        },
      });

      const staleTimeWrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={staleTimeQueryClient}>
          {children}
        </QueryClientProvider>
      );

      // Act - First fetch to populate cache
      const { result: result1 } = renderHook(() => useLMStudioModels(), {
        wrapper: staleTimeWrapper,
      });

      // Enable the query and wait for success
      result1.current.refetch();

      await waitFor(() => {
        expect(result1.current.isSuccess).toBe(true);
      });

      // Clear the mock to test stale time
      vi.clearAllMocks();

      // Act - Second hook instance should use cached data due to stale time
      const { result: result2 } = renderHook(() => useLMStudioModels(), {
        wrapper: staleTimeWrapper,
      });

      // Give it a moment to potentially call the service
      await new Promise(resolve => setTimeout(resolve, 100));

      // Assert - should not have called the service again due to stale time
      expect(fetchLMStudioModels).not.toHaveBeenCalled();

      // The second hook should have the cached data available
      expect(result2.current.data).toEqual(mockModels);
    });

    it('should be disabled by default', () => {
      // Act
      const { result } = renderHook(() => useLMStudioModels(), { wrapper });

      // Assert
      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBeNull();
      expect(fetchLMStudioModels).not.toHaveBeenCalled();
    });
  });
});
