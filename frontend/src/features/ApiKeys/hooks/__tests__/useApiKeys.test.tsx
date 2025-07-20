import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import { JSX, ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// Import generated client types
import type { ApiKeyCreated, ApiKeyList, ApiKeyRevoked } from '@/lib/api-client';
import { CancelablePromise } from '@/lib/api-client';

import {
  mockGeneratedApiKeyCreate,
  mockGeneratedApiKeyCreated,
  mockGeneratedApiKeyInfo,
  mockGeneratedApiKeyList,
} from '@/test/factories';
import { createMockError } from '@/test/utils';

// Mock the generated API client
vi.mock('@/lib/api-client', () => ({
  ApiKeysService: {
    listApiKeysApiV1UsersMeApiKeysGet: vi.fn(),
    createApiKeyApiV1UsersMeApiKeysPost: vi.fn(),
    revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete: vi.fn(),
  },
  CancelablePromise: vi.fn(),
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

import { ApiKeysService } from '@/lib/api-client';
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from '../useApiKeys';

describe('useApiKeys Hooks', () => {
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

  describe('useApiKeys', () => {
    it('should fetch API keys successfully', async () => {
      // Arrange
      const mockKeys = [
        mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1' }),
        mockGeneratedApiKeyInfo({ id: 2, label: 'Key 2' }),
      ];
      const mockResponse = mockGeneratedApiKeyList({ keys: mockKeys, total: 2 });
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue(
        mockResponse
      );

      // Act
      const { result } = renderHook(() => useApiKeys(), { wrapper });

      // Assert
      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockKeys);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).toHaveBeenCalledTimes(1);
    });

    it('should handle loading state correctly', async () => {
      // Arrange
      let resolvePromise: (value: ApiKeyList) => void = () => {};
      const promise = new Promise<ApiKeyList>(resolve => {
        resolvePromise = resolve;
      });

      // Mock the API service to return a promise that we can control
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockReturnValue(
        promise as unknown as CancelablePromise<ApiKeyList>
      );

      // Act
      const { result } = renderHook(() => useApiKeys(), { wrapper });

      // Assert - should be loading initially
      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBeNull();

      // Resolve the promise with valid data
      resolvePromise(mockGeneratedApiKeyList({ keys: [], total: 0 }));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Verify the data is properly set
      expect(result.current.data).toEqual([]);
      expect(result.current.isSuccess).toBe(true);
    });

    it('should handle error state correctly', async () => {
      // Arrange
      const error = createMockError(500, 'Internal Server Error');
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockRejectedValue(
        error
      );

      // Act
      const { result } = renderHook(() => useApiKeys(), { wrapper });

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
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockRejectedValue(
        error
      );

      // Act
      const { result } = renderHook(() => useApiKeys(), { wrapper });

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

    it('should retry only once on failure', async () => {
      // Arrange
      const error = createMockError(500, 'Server Error');
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockRejectedValue(
        error
      );

      // Act
      const { result } = renderHook(() => useApiKeys(), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      // Should have been called twice (initial + 1 retry)
      expect(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).toHaveBeenCalledTimes(2);
    });

    it('should handle empty key list', async () => {
      // Arrange
      const mockResponse = mockGeneratedApiKeyList({ keys: [], total: 0 });
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue(
        mockResponse
      );

      // Act
      const { result } = renderHook(() => useApiKeys(), { wrapper });

      // Assert
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual([]);
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('useCreateApiKey', () => {
    it('should create API key successfully', async () => {
      // Arrange
      const mockRequest = mockGeneratedApiKeyCreate({
        label: 'New Key',
        expires_in_days: 30,
      });
      const mockResponse = mockGeneratedApiKeyCreated({
        token: 'test-token-123',
        api_key: mockGeneratedApiKeyInfo({ id: 1, label: 'New Key' }),
      });
      vi.mocked(ApiKeysService.createApiKeyApiV1UsersMeApiKeysPost).mockResolvedValue(
        mockResponse
      );

      // Act
      const { result } = renderHook(() => useCreateApiKey(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Assert
      expect(result.current.data).toEqual(mockResponse);
      expect(ApiKeysService.createApiKeyApiV1UsersMeApiKeysPost).toHaveBeenCalledWith({
        requestBody: mockRequest,
      });
      expect(mockShowSuccessNotification).toHaveBeenCalledWith(
        'API key created successfully!'
      );
    });

    it('should update cache with new key on success', async () => {
      // Arrange
      const existingKeys = [mockGeneratedApiKeyInfo({ id: 1, label: 'Existing Key' })];
      const mockRequest = mockGeneratedApiKeyCreate({ label: 'Cache Test Key' });
      const mockResponse = mockGeneratedApiKeyCreated({
        token: 'test-token-456',
        api_key: mockGeneratedApiKeyInfo({ id: 2, label: 'Cache Test Key' }),
      });

      // Mock the list API to return existing keys initially
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: existingKeys,
        total: existingKeys.length,
      });

      // Mock the create API to return the new key
      vi.mocked(ApiKeysService.createApiKeyApiV1UsersMeApiKeysPost).mockResolvedValue(
        mockResponse
      );

      // Act
      const { result } = renderHook(
        () => {
          const apiKeys = useApiKeys();
          const createApiKey = useCreateApiKey();
          return { apiKeys, createApiKey };
        },
        {
          wrapper,
        }
      );

      // Wait for initial data to load
      await waitFor(() => {
        expect(result.current.apiKeys.isSuccess).toBe(true);
      });

      // Verify initial cache state through the query hook
      expect(result.current.apiKeys.data).toEqual(existingKeys);

      await act(async () => {
        result.current.createApiKey.mutate(mockRequest);
      });

      await waitFor(() => {
        expect(result.current.createApiKey.isSuccess).toBe(true);
      });

      // Verify cache was updated through the query hook
      expect(result.current.apiKeys.data).toBeTruthy();
      expect(result.current.apiKeys.data).toHaveLength(2);
      expect(result.current.apiKeys.data?.[0]).toEqual(mockResponse.api_key);
      expect(result.current.apiKeys.data?.[1]).toEqual(existingKeys[0]);
    });

    it('should handle error and show notification', async () => {
      // Arrange
      const mockRequest = mockGeneratedApiKeyCreate({ label: 'Error Key' });
      const error = createMockError(400, 'Bad Request');
      vi.mocked(ApiKeysService.createApiKeyApiV1UsersMeApiKeysPost).mockRejectedValue(
        error
      );

      // Act
      const { result } = renderHook(() => useCreateApiKey(), { wrapper });

      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // Assert
      expect(result.current.error).toBe(error);
      expect(mockShowErrorNotification).toHaveBeenCalledWith(
        error,
        'Failed to create API key'
      );
    });

    it('should invalidate queries on error', async () => {
      // Arrange
      const mockRequest = mockGeneratedApiKeyCreate({ label: 'Invalidate Test' });
      const error = createMockError(500, 'Server Error');
      vi.mocked(ApiKeysService.createApiKeyApiV1UsersMeApiKeysPost).mockRejectedValue(
        error
      );

      // Track query invalidation
      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

      // Act
      const { result } = renderHook(() => useCreateApiKey(), { wrapper });

      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // Assert
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['api-keys'] });
    });

    it('should handle pending state correctly', async () => {
      // Arrange
      const mockRequest = mockGeneratedApiKeyCreate({ label: 'Pending Key' });
      let resolvePromise!: (value: ApiKeyCreated) => void;
      const promise = new Promise<ApiKeyCreated>(resolve => {
        resolvePromise = resolve;
      });
      vi.mocked(ApiKeysService.createApiKeyApiV1UsersMeApiKeysPost).mockReturnValue(
        promise as unknown as CancelablePromise<ApiKeyCreated>
      );

      // Act
      const { result } = renderHook(() => useCreateApiKey(), { wrapper });

      // Start the mutation
      act(() => {
        result.current.mutate(mockRequest);
      });

      // Wait until the mutation is in pending state
      await waitFor(() => {
        expect(result.current.isPending).toBe(true);
      });
      expect(result.current.data).toBeUndefined();

      // Now resolve the promise
      act(() => {
        resolvePromise(
          mockGeneratedApiKeyCreated({
            token: 'test-token',
            api_key: mockGeneratedApiKeyInfo({ id: 1, label: 'Pending Key' }),
          })
        );
      });

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });
    });
  });

  describe('useRevokeApiKey', () => {
    it('should revoke API key successfully', async () => {
      // Arrange
      const keyId = 1;
      const mockResponse: ApiKeyRevoked = {
        success: true,
        message: 'API key revoked successfully',
      };
      vi.mocked(
        ApiKeysService.revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete
      ).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useRevokeApiKey(), { wrapper });

      result.current.mutate(keyId);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Assert
      expect(
        ApiKeysService.revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete
      ).toHaveBeenCalledWith({ keyId });
      expect(mockShowSuccessNotification).toHaveBeenCalledWith(
        'API key revoked successfully!'
      );
    });

    it('should update cache to mark key as inactive on success', async () => {
      // Arrange
      const existingKeys = [
        mockGeneratedApiKeyInfo({ id: 1, label: 'Key 1', is_active: true }),
        mockGeneratedApiKeyInfo({ id: 2, label: 'Key 2', is_active: true }),
      ];
      const keyId = 1;
      const mockResponse: ApiKeyRevoked = {
        success: true,
        message: 'API key revoked successfully',
      };

      // Mock the list API to return existing keys initially
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: existingKeys,
        total: existingKeys.length,
      });

      // Mock the revoke API to succeed
      vi.mocked(
        ApiKeysService.revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete
      ).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(
        () => {
          const apiKeys = useApiKeys();
          const revokeApiKey = useRevokeApiKey();
          return { apiKeys, revokeApiKey };
        },
        {
          wrapper,
        }
      );

      // Wait for initial data to load
      await waitFor(() => {
        expect(result.current.apiKeys.isSuccess).toBe(true);
      });

      // Verify initial cache state through the query hook
      expect(result.current.apiKeys.data).toEqual(existingKeys);

      await act(async () => {
        result.current.revokeApiKey.mutate(keyId);
      });

      await waitFor(() => {
        expect(result.current.revokeApiKey.isSuccess).toBe(true);
      });

      // Verify cache was updated through the query hook
      expect(result.current.apiKeys.data).toBeTruthy();
      expect(result.current.apiKeys.data).toHaveLength(2);
      expect(result.current.apiKeys.data?.[0]).toEqual({
        ...existingKeys[0],
        is_active: false,
      });
      expect(result.current.apiKeys.data?.[1]).toEqual(existingKeys[1]);
    });

    it('should handle error and show notification', async () => {
      // Arrange
      const keyId = 1;
      const error = createMockError(404, 'Not Found');
      vi.mocked(
        ApiKeysService.revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete
      ).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useRevokeApiKey(), { wrapper });

      result.current.mutate(keyId);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // Assert
      expect(result.current.error).toBe(error);
      expect(mockShowErrorNotification).toHaveBeenCalledWith(
        error,
        'Failed to revoke API key'
      );
    });

    it('should invalidate queries on error', async () => {
      // Arrange
      const keyId = 1;
      const error = createMockError(500, 'Server Error');
      vi.mocked(
        ApiKeysService.revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete
      ).mockRejectedValue(error);

      // Track query invalidation
      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

      // Act
      const { result } = renderHook(() => useRevokeApiKey(), { wrapper });

      result.current.mutate(keyId);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // Assert
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['api-keys'] });
    });

    it('should handle pending state correctly', async () => {
      // Arrange
      const keyId = 1;
      let resolvePromise!: (value: ApiKeyRevoked) => void;
      const promise = new Promise<ApiKeyRevoked>(resolve => {
        resolvePromise = resolve;
      });
      vi.mocked(
        ApiKeysService.revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete
      ).mockReturnValue(promise as unknown as CancelablePromise<ApiKeyRevoked>);

      // Act
      const { result } = renderHook(() => useRevokeApiKey(), { wrapper });

      // Start the mutation
      act(() => {
        result.current.mutate(keyId);
      });

      // Wait until the mutation is in pending state
      await waitFor(() => {
        expect(result.current.isPending).toBe(true);
      });
      expect(result.current.data).toBeUndefined();

      // Now resolve the promise
      act(() => {
        resolvePromise({
          success: true,
          message: 'API key revoked successfully',
        });
      });

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });
    });

    it('should handle error and invalidate queries', async () => {
      // Arrange
      const keyId = 1;
      const error = createMockError(500, 'Server Error');
      vi.mocked(
        ApiKeysService.revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete
      ).mockRejectedValue(error);

      // Track query invalidation
      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

      // Act
      const { result } = renderHook(() => useRevokeApiKey(), { wrapper });

      result.current.mutate(keyId);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // Assert
      expect(result.current.error).toBe(error);
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['api-keys'] });
    });
  });
});
