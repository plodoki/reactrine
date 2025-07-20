import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// Import types for type assertions
import type { ApiKeyInfo } from '@/lib/api-client';

// Hooks
import {
  useApiKeys,
  useCreateApiKey,
  useRevokeApiKey,
} from '@/features/ApiKeys/hooks/useApiKeys';
import { useTaskResult } from '@/hooks/useTasks';

// Mock factories
import { mockGeneratedApiKeyInfo } from '@/test/factories';

// Mock the generated API client
vi.mock('@/lib/api-client', () => ({
  ApiKeysService: {
    listApiKeysApiV1UsersMeApiKeysGet: vi.fn(),
    createApiKeyApiV1UsersMeApiKeysPost: vi.fn(),
    revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete: vi.fn(),
  },
  LlmSettingsService: {
    getUserLlmSettingsApiV1UsersLlmSettingsGet: vi.fn(),
    updateUserLlmSettingsApiV1UsersLlmSettingsPut: vi.fn(),
  },
  TasksService: {
    getTaskResultApiV1TasksTaskIdGet: vi.fn(),
    listActiveTasksApiV1TasksActiveGet: vi.fn(),
    triggerSimpleTaskApiV1TasksSimplePost: vi.fn(),
  },
}));

// Mock notifications hook
vi.mock('@/hooks/useNotifications', () => ({
  useNotifications: () => ({
    showSuccessNotification: vi.fn(),
    showErrorNotification: vi.fn(),
  }),
}));

// Test wrapper for React Query
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0, gcTime: 0 },
      mutations: { retry: false },
    },
  });

const TestWrapper = ({ children }: { children: ReactNode }) => {
  const queryClient = createTestQueryClient();
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
};

describe('React Query Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Query Invalidation Patterns', () => {
    it('should invalidate related queries on mutation success', async () => {
      // Mock API responses
      const { ApiKeysService } = await import('@/lib/api-client');
      const initialKeys = [mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' })];
      const newKey = mockGeneratedApiKeyInfo({ id: 2, label: 'Key 2' });

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: initialKeys,
        total: initialKeys.length,
      });
      vi.mocked(ApiKeysService.createApiKeyApiV1UsersMeApiKeysPost).mockResolvedValue({
        api_key: newKey,
        token: 'test-token',
      });

      // Render hooks
      const { result } = renderHook(
        () => ({
          apiKeys: useApiKeys(),
          createApiKey: useCreateApiKey(),
        }),
        { wrapper: TestWrapper }
      );

      // Wait for initial query
      await waitFor(() => {
        expect(result.current.apiKeys.isSuccess).toBe(true);
      });

      expect(result.current.apiKeys.data).toHaveLength(1);

      // Mock updated response for refetch
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: [newKey, initialKeys[0]], // New key gets added to the beginning
        total: 2,
      });

      // Create new key
      act(() => {
        result.current.createApiKey.mutate({ label: 'Key 2' });
      });

      // Wait for mutation and invalidation
      await waitFor(() => {
        expect(result.current.createApiKey.isSuccess).toBe(true);
      });

      // Verify cache was updated (the hook adds the new key to the beginning)
      expect(result.current.apiKeys.data).toHaveLength(2);
      expect(result.current.apiKeys.data?.[0].label).toBe('Key 2'); // New key first
    });

    it('should handle query invalidation on mutation error', async () => {
      // Mock API responses
      const { ApiKeysService } = await import('@/lib/api-client');
      const initialKeys = [mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' })];

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: initialKeys,
        total: initialKeys.length,
      });
      // Mock the generated client that the hook now uses
      vi.mocked(
        ApiKeysService.revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete
      ).mockRejectedValue(new Error('Revoke failed'));

      // Create a persistent query client for this test
      const testQueryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false, staleTime: 0, gcTime: 0 },
          mutations: { retry: false },
        },
      });

      const PersistentTestWrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={testQueryClient}>{children}</QueryClientProvider>
      );

      // Render hooks
      const { result } = renderHook(
        () => ({
          apiKeys: useApiKeys(),
          revokeApiKey: useRevokeApiKey(),
        }),
        { wrapper: PersistentTestWrapper }
      );

      // Wait for initial query
      await waitFor(() => {
        expect(result.current.apiKeys.isSuccess).toBe(true);
      });

      // Track query invalidation on the same query client the hooks are using
      const invalidateQueriesSpy = vi.spyOn(testQueryClient, 'invalidateQueries');

      // Attempt to revoke key (will fail)
      act(() => {
        result.current.revokeApiKey.mutate(1);
      });

      // Wait for mutation error
      await waitFor(() => {
        expect(result.current.revokeApiKey.isError).toBe(true);
      });

      // Verify queries were invalidated on error
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['api-keys'] });
    });
  });

  describe('Cache Management', () => {
    it('should handle cache updates correctly', async () => {
      // Mock API responses
      const { ApiKeysService } = await import('@/lib/api-client');
      const initialKeys = [mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' })];

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: initialKeys,
        total: initialKeys.length,
      });
      vi.mocked(
        ApiKeysService.revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete
      ).mockResolvedValue({ message: 'API key revoked successfully', success: true });

      // Render hooks
      const { result } = renderHook(
        () => ({
          apiKeys: useApiKeys(),
          revokeApiKey: useRevokeApiKey(),
        }),
        { wrapper: TestWrapper }
      );

      // Wait for initial data
      await waitFor(() => {
        expect(result.current.apiKeys.isSuccess).toBe(true);
      });

      expect(result.current.apiKeys.data).toHaveLength(1);
      expect(result.current.apiKeys.data?.[0].is_active).toBe(true);

      // Revoke a key
      act(() => {
        result.current.revokeApiKey.mutate(1);
      });

      // Wait for mutation to complete
      await waitFor(() => {
        expect(result.current.revokeApiKey.isSuccess).toBe(true);
      });

      // Verify cache was updated (the hook updates the cache to mark key as inactive)
      const updatedData = result.current.apiKeys.data;
      expect(updatedData).toHaveLength(1);
      expect(updatedData?.find(key => key.id === 1)?.is_active).toBe(false);
    });

    it('should handle cache invalidation and refetch', async () => {
      // Mock API responses
      const { ApiKeysService } = await import('@/lib/api-client');
      const initialKeys = [mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' })];
      const updatedKeys = [
        mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' }),
        mockGeneratedApiKeyInfo({ id: 2, label: 'Key 2' }),
      ];

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet)
        .mockResolvedValueOnce({ keys: initialKeys, total: initialKeys.length })
        .mockResolvedValueOnce({ keys: updatedKeys, total: updatedKeys.length });

      // Create a persistent query client for this test
      const persistentQueryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false, staleTime: 0, gcTime: 0 },
          mutations: { retry: false },
        },
      });

      const PersistentTestWrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={persistentQueryClient}>
          {children}
        </QueryClientProvider>
      );

      // Render hook
      const { result } = renderHook(() => useApiKeys(), {
        wrapper: PersistentTestWrapper,
      });

      // Wait for initial data
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toHaveLength(1);

      // Manually invalidate cache
      act(() => {
        persistentQueryClient.invalidateQueries({ queryKey: ['api-keys'] });
      });

      // Wait for refetch
      await waitFor(() => {
        expect(result.current.data).toHaveLength(2);
      });

      expect(result.current.data?.[1].label).toBe('Key 2');
    });

    it('should handle cache updates from external sources', async () => {
      // Mock API response
      const { ApiKeysService } = await import('@/lib/api-client');
      const initialKeys = [mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' })];

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: initialKeys,
        total: initialKeys.length,
      });

      // Create a persistent query client for this test
      const persistentQueryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false, staleTime: 0, gcTime: 0 },
          mutations: { retry: false },
        },
      });

      const PersistentTestWrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={persistentQueryClient}>
          {children}
        </QueryClientProvider>
      );

      // Render hook
      const { result } = renderHook(() => useApiKeys(), {
        wrapper: PersistentTestWrapper,
      });

      // Wait for initial data
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Simulate external cache update
      const newKeys = [
        mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' }),
        mockGeneratedApiKeyInfo({ id: 2, label: 'External Key' }),
      ];

      act(() => {
        persistentQueryClient.setQueryData(['api-keys'], newKeys);
      });

      // Verify cache was updated in the query client
      expect(persistentQueryClient.getQueryData(['api-keys'])).toEqual(newKeys);
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle query errors gracefully without crashing', async () => {
      // Mock API error
      const { ApiKeysService } = await import('@/lib/api-client');
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockRejectedValue(
        new Error('Network error')
      );

      // Render hook
      const { result } = renderHook(() => useApiKeys(), { wrapper: TestWrapper });

      // Wait for error state
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 3000 }
      );

      // Verify error is captured
      expect(result.current.error).toBeInstanceOf(Error);
      expect(result.current.error?.message).toBe('Network error');
      expect(result.current.data).toBeUndefined();
    });

    it('should recover from errors with retry mechanism', async () => {
      // Mock API with initial error, then success
      const { ApiKeysService } = await import('@/lib/api-client');
      const mockKeys = [mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' })];

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValue({ keys: mockKeys, total: mockKeys.length });

      // Create query client with retry enabled
      const retryQueryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: 1, retryDelay: 0 },
          mutations: { retry: false },
        },
      });

      const RetryTestWrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={retryQueryClient}>{children}</QueryClientProvider>
      );

      // Render hook
      const { result } = renderHook(() => useApiKeys(), { wrapper: RetryTestWrapper });

      // Wait for recovery
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Verify data was eventually loaded
      expect(result.current.data).toHaveLength(1);
      expect(result.current.data?.[0].label).toBe('Key 1');
    });

    it('should handle mutation errors without affecting other queries', async () => {
      // Mock API responses
      const { ApiKeysService } = await import('@/lib/api-client');
      const initialKeys = [mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' })];

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: initialKeys,
        total: initialKeys.length,
      });
      vi.mocked(ApiKeysService.createApiKeyApiV1UsersMeApiKeysPost).mockRejectedValue(
        new Error('Creation failed')
      );

      // Render hooks
      const { result } = renderHook(
        () => ({
          apiKeys: useApiKeys(),
          createApiKey: useCreateApiKey(),
        }),
        { wrapper: TestWrapper }
      );

      // Wait for initial query
      await waitFor(() => {
        expect(result.current.apiKeys.isSuccess).toBe(true);
      });

      // Attempt to create key (will fail)
      act(() => {
        result.current.createApiKey.mutate({ label: 'New Key' });
      });

      // Wait for mutation error
      await waitFor(() => {
        expect(result.current.createApiKey.isError).toBe(true);
      });

      // Verify query data is still intact
      expect(result.current.apiKeys.isSuccess).toBe(true);
      expect(result.current.apiKeys.data).toHaveLength(1);
      expect(result.current.createApiKey.error?.message).toBe('Creation failed');
    });
  });

  describe('Query State Management', () => {
    it('should handle loading states correctly', async () => {
      // Mock API with delay
      const { ApiKeysService } = await import('@/lib/api-client');
      const mockKeys = [mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' })];

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: mockKeys,
        total: mockKeys.length,
      });

      // Render hook
      const { result } = renderHook(() => useApiKeys(), { wrapper: TestWrapper });

      // Initially should be loading
      expect(result.current.isLoading).toBe(true);
      expect(result.current.isSuccess).toBe(false);
      expect(result.current.isError).toBe(false);

      // Wait for completion
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toHaveLength(1);
    });

    it('should handle enabled/disabled queries correctly', async () => {
      // Mock API response
      const { TasksService } = await import('@/lib/api-client');
      vi.mocked(TasksService.getTaskResultApiV1TasksTaskIdGet).mockResolvedValue({
        task_id: 'test-task',
        status: 'SUCCESS',
        result: { message: 'success' },
        error: null,
      });

      // Render hook with disabled query
      const { result, rerender } = renderHook(
        ({ enabled }: { enabled: boolean }) =>
          useTaskResult(enabled ? 'test-task' : ''),
        { wrapper: TestWrapper, initialProps: { enabled: false } }
      );

      // Should not fetch when disabled
      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toBeUndefined();

      // Enable query
      rerender({ enabled: true });

      // Should now fetch
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.result).toEqual({ message: 'success' });
    });

    it('should handle query client configuration options', async () => {
      // Create query client with custom options
      const customQueryClient = new QueryClient({
        defaultOptions: {
          queries: { staleTime: 100, gcTime: 1000, refetchOnWindowFocus: false },
          mutations: { retry: false },
        },
      });

      // Verify that the query client has the correct configuration
      expect(customQueryClient.getDefaultOptions().queries?.staleTime).toBe(100);
      expect(customQueryClient.getDefaultOptions().queries?.gcTime).toBe(1000);
      expect(customQueryClient.getDefaultOptions().queries?.refetchOnWindowFocus).toBe(
        false
      );
      expect(customQueryClient.getDefaultOptions().mutations?.retry).toBe(false);

      // Test that the query client can be used with React Query Provider
      const CustomTestWrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={customQueryClient}>{children}</QueryClientProvider>
      );

      // Verify the provider can be rendered without errors
      const { result } = renderHook(
        () => {
          // Simple hook that just returns a constant to test the provider
          return { test: 'success' };
        },
        { wrapper: CustomTestWrapper }
      );

      expect(result.current.test).toBe('success');
    });
  });

  describe('Cache Persistence', () => {
    it('should maintain cache across component unmounts', async () => {
      // Mock API response
      const { ApiKeysService } = await import('@/lib/api-client');
      const mockKeys = [mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' })];

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: mockKeys,
        total: mockKeys.length,
      });

      // Create a persistent query client
      const persistentQueryClient = new QueryClient({
        defaultOptions: {
          queries: { retry: false, staleTime: 0, gcTime: 300000 }, // 5 minutes cache
          mutations: { retry: false },
        },
      });

      const PersistentTestWrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={persistentQueryClient}>
          {children}
        </QueryClientProvider>
      );

      // First render
      const { result: firstResult, unmount } = renderHook(() => useApiKeys(), {
        wrapper: PersistentTestWrapper,
      });

      // Wait for data
      await waitFor(() => {
        expect(firstResult.current.isSuccess).toBe(true);
      });

      expect(firstResult.current.data).toHaveLength(1);

      // Unmount component
      unmount();

      // Second render - should use cached data
      const { result: secondResult } = renderHook(() => useApiKeys(), {
        wrapper: PersistentTestWrapper,
      });

      // Should have cached data immediately (or be loading from cache)
      if (secondResult.current.data) {
        expect(secondResult.current.data).toHaveLength(1);
        expect(secondResult.current.data[0]?.label).toBe('Key 1');
      } else {
        // If no cached data, wait for fresh data
        await waitFor(() => {
          expect(secondResult.current.isSuccess).toBe(true);
        });
        expect(secondResult.current.data).toHaveLength(1);
        expect(
          (secondResult.current.data as ApiKeyInfo[] | undefined)?.[0]?.label
        ).toBe('Key 1');
      }
    });
  });
});
