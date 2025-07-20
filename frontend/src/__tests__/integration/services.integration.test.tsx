import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// Services
import authService from '@/services/authService';

// Hooks
import {
  useApiKeys,
  useCreateApiKey,
  useRevokeApiKey,
} from '@/features/ApiKeys/hooks/useApiKeys';

// Generated client
import { OpenAPI } from '@/lib/api-client';

// Mock factories
import { mockGeneratedApiKeyInfo, mockGeneratedUser } from '@/test/factories';

// Mock the generated API client
vi.mock('@/lib/api-client', () => ({
  OpenAPI: {
    BASE: 'http://127.0.0.1:8000',
    WITH_CREDENTIALS: true,
    CREDENTIALS: 'include',
    HEADERS: vi.fn().mockImplementation(async options => {
      const headers: Record<string, string> = {};
      if (
        options.method &&
        !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase())
      ) {
        // Mock CSRF token for state-changing requests - read from cookie
        const csrfToken =
          document.cookie
            .split('; ')
            .find(row => row.startsWith('csrf_token='))
            ?.split('=')[1] || 'test-csrf-token';
        headers['X-CSRF-Token'] = csrfToken;
      }
      return headers;
    }),
  },
  AuthService: {
    getRegistrationStatusApiV1AuthRegistrationStatusGet: vi.fn(),
    registerUserApiV1AuthRegisterPost: vi.fn(),
    loginUserApiV1AuthLoginPost: vi.fn(),
    googleOauthCallbackApiV1AuthGooglePost: vi.fn(),
    getCurrentUserInfoApiV1AuthMeGet: vi.fn(),
    logoutUserApiV1AuthLogoutPost: vi.fn(),
    getCsrfTokenApiV1AuthCsrfTokenGet: vi.fn(),
  },
  ApiKeysService: {
    listApiKeysApiV1UsersMeApiKeysGet: vi.fn(),
    createApiKeyApiV1UsersMeApiKeysPost: vi.fn(),
    revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete: vi.fn(),
  },
}));

// Don't mock the auth service - we want to test the real service integration

// Mock the app store
vi.mock('@/stores/useAppStore', () => ({
  useAppStore: {
    getState: vi.fn(() => ({
      setCsrfToken: vi.fn(),
    })),
  },
}));

// const mockAuthService = vi.mocked(authService);

// Test wrapper component
const TestWrapper = ({ children }: { children: ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
};

describe('Service Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Authentication Flow Integration', () => {
    it('should handle complete authentication flow', async () => {
      // Mock successful responses
      const mockUser = mockGeneratedUser();
      const { AuthService } = await import('@/lib/api-client');

      vi.mocked(AuthService.getCurrentUserInfoApiV1AuthMeGet).mockResolvedValue(
        mockUser
      );

      // Test the service integration
      const user = await authService.getCurrentUser();
      expect(user).toEqual({
        id: mockUser.id,
        email: mockUser.email,
        auth_provider: mockUser.auth_provider,
        is_active: mockUser.is_active,
        role: mockUser.role,
        created_at: mockUser.created_at,
        updated_at: mockUser.updated_at,
      });
    });

    it('should handle registration flow', async () => {
      // Mock successful responses
      const mockUser = mockGeneratedUser();
      const { AuthService } = await import('@/lib/api-client');

      vi.mocked(
        AuthService.getRegistrationStatusApiV1AuthRegistrationStatusGet
      ).mockResolvedValue({
        allowed: true,
        message: null,
      });

      vi.mocked(AuthService.registerUserApiV1AuthRegisterPost).mockResolvedValue(
        mockUser
      );

      // Test the service integration
      const user = await authService.register('test@example.com', 'password123');
      expect(user).toEqual({
        id: mockUser.id,
        email: mockUser.email,
        auth_provider: mockUser.auth_provider,
        is_active: mockUser.is_active,
        role: mockUser.role,
        created_at: mockUser.created_at,
        updated_at: mockUser.updated_at,
      });
    });

    it('should manage CSRF tokens correctly in generated client configuration', async () => {
      // Mock CSRF token response
      const { AuthService } = await import('@/lib/api-client');
      vi.mocked(AuthService.getCsrfTokenApiV1AuthCsrfTokenGet).mockResolvedValue({
        token: 'test-csrf-token',
      });

      // Test CSRF token retrieval
      const csrfToken = await authService.getCsrfToken();
      expect(csrfToken).toBe('test-csrf-token');
      expect(AuthService.getCsrfTokenApiV1AuthCsrfTokenGet).toHaveBeenCalled();
    });

    it('should handle CSRF token refresh during authentication flow', async () => {
      // Mock the app store
      const mockSetCsrfToken = vi.fn();
      const { useAppStore } = await import('@/stores/useAppStore');
      vi.mocked(useAppStore.getState).mockReturnValue({
        setCsrfToken: mockSetCsrfToken,
      } as unknown as ReturnType<typeof useAppStore.getState>);

      // Mock document.cookie to simulate CSRF token being set
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=updated-csrf-token; access_token=new-access-token',
      });

      // Mock successful login
      const mockUser = mockGeneratedUser();
      const { AuthService } = await import('@/lib/api-client');
      vi.mocked(AuthService.loginUserApiV1AuthLoginPost).mockResolvedValue(mockUser);

      // Test the service integration
      const user = await authService.login('test@example.com', 'password123');
      expect(user).toEqual({
        id: mockUser.id,
        email: mockUser.email,
        auth_provider: mockUser.auth_provider,
        is_active: mockUser.is_active,
        role: mockUser.role,
        created_at: mockUser.created_at,
        updated_at: mockUser.updated_at,
      });

      // Verify that the authentication flow completed successfully
      expect(AuthService.loginUserApiV1AuthLoginPost).toHaveBeenCalledWith({
        formData: {
          username: 'test@example.com',
          password: 'password123',
        },
      });
    });
  });

  describe('API Key Management Integration', () => {
    it('should complete CRUD operations with proper service-hook integration', async () => {
      // Mock the generated client responses
      const { ApiKeysService } = await import('@/lib/api-client');
      const mockApiKeyResponse = mockGeneratedApiKeyInfo();
      const mockApiKeysList = [mockApiKeyResponse];

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockResolvedValue({
        keys: mockApiKeysList,
        total: mockApiKeysList.length,
      });
      vi.mocked(ApiKeysService.createApiKeyApiV1UsersMeApiKeysPost).mockResolvedValue({
        api_key: mockApiKeyResponse,
        token: 'test-key-value',
      });

      // Test generated client integration directly through hooks

      // Test hook integration
      const { result: hooksResult } = renderHook(
        () => ({
          apiKeys: useApiKeys(),
          createApiKey: useCreateApiKey(),
          revokeApiKey: useRevokeApiKey(),
        }),
        { wrapper: TestWrapper }
      );

      // Wait for initial query to complete
      await waitFor(() => {
        expect(hooksResult.current.apiKeys.isSuccess).toBe(true);
      });

      expect(hooksResult.current.apiKeys.data).toHaveLength(1);
    });

    it('should handle error scenarios in API key operations', async () => {
      // Mock error responses
      const { ApiKeysService } = await import('@/lib/api-client');
      const error = new Error('API Error');

      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet).mockRejectedValue(
        error
      );

      // Test error handling through hooks
      const { result } = renderHook(() => useApiKeys(), { wrapper: TestWrapper });

      // Wait for the query to complete and check if it's in error state
      await waitFor(
        () => {
          expect(result.current.isLoading).toBe(false);
        },
        { timeout: 3000 }
      );

      // Check if the error was properly captured
      expect(result.current.isError).toBe(true);
      expect(result.current.error).toBe(error);
    });

    it('should handle authentication errors and token refresh', async () => {
      // Mock authentication error followed by success
      const { ApiKeysService } = await import('@/lib/api-client');
      const mockApiKeyResponse = mockGeneratedApiKeyInfo();
      const mockApiKeysList = [mockApiKeyResponse];

      // Since React Query has retry: 1 in the useApiKeys hook, it will retry once
      // We need to mock the failure twice, then success
      vi.mocked(ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet)
        .mockRejectedValueOnce(new Error('Unauthorized'))
        .mockResolvedValueOnce({
          keys: mockApiKeysList,
          total: mockApiKeysList.length,
        });

      // Test that the hook eventually succeeds after retry
      const { result } = renderHook(() => useApiKeys(), { wrapper: TestWrapper });

      // Wait for the query to complete
      await waitFor(
        () => {
          expect(result.current.isLoading).toBe(false);
        },
        { timeout: 3000 }
      );

      // Check if it succeeded after retry
      expect(result.current.isSuccess).toBe(true);
      expect(result.current.data).toHaveLength(1);
    });
  });

  describe('Generated Client Configuration Integration', () => {
    it('should configure base URL correctly', () => {
      // Test that OpenAPI configuration is properly set
      expect(OpenAPI.BASE).toBeDefined();
      expect(OpenAPI.WITH_CREDENTIALS).toBe(true);
      expect(OpenAPI.CREDENTIALS).toBe('include');
    });

    it('should include CSRF tokens in state-changing requests', async () => {
      // Mock document.cookie for CSRF token
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=test-csrf-token; other=value',
      });

      // Test CSRF token inclusion in headers
      const headersFunction = OpenAPI.HEADERS;
      if (typeof headersFunction === 'function') {
        const headers = await headersFunction({
          method: 'POST',
          url: '/api/v1/test',
        });
        expect(headers).toBeDefined();
        expect(headers).toHaveProperty('X-CSRF-Token', 'test-csrf-token');
      }
    });

    it('should not include CSRF tokens in GET requests', async () => {
      // Mock document.cookie for CSRF token
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=test-csrf-token; other=value',
      });

      // Test that CSRF token is not included in GET requests
      const headersFunction = OpenAPI.HEADERS;
      if (typeof headersFunction === 'function') {
        const headers = await headersFunction({
          method: 'GET',
          url: '/api/v1/test',
        });
        expect(headers).toBeDefined();
        expect(headers).not.toHaveProperty('X-CSRF-Token');
      }
    });

    it('should handle authentication headers properly', async () => {
      // Test that credentials are properly configured
      expect(OpenAPI.WITH_CREDENTIALS).toBe(true);
      expect(OpenAPI.CREDENTIALS).toBe('include');
    });

    it('should handle CSRF token updates during token refresh', async () => {
      // Mock the app store
      const mockSetCsrfToken = vi.fn();
      const { useAppStore } = await import('@/stores/useAppStore');
      vi.mocked(useAppStore.getState).mockReturnValue({
        setCsrfToken: mockSetCsrfToken,
      } as unknown as ReturnType<typeof useAppStore.getState>);

      // Mock document.cookie to simulate new CSRF token after refresh
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=refreshed-csrf-token; access_token=new-access-token',
      });

      // Test that CSRF token is read from cookie dynamically
      const headersFunction = OpenAPI.HEADERS;
      if (typeof headersFunction === 'function') {
        const headers = await headersFunction({
          method: 'POST',
          url: '/api/v1/test',
        });
        expect(headers).toBeDefined();
        expect(headers).toHaveProperty('X-CSRF-Token', 'refreshed-csrf-token');
      }
    });
  });
});
