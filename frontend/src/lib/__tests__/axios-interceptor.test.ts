import axios, {
  AxiosAdapter,
  AxiosError,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// Import the interceptor (this will attach interceptors to axios)
import '@/lib/axios-interceptor';

// Import one of the generated service calls that uses the global axios instance
import { ApiKeysService } from '@/lib/api-client';

// Mock the app store
vi.mock('@/stores/useAppStore', () => ({
  useAppStore: {
    getState: vi.fn(() => ({
      setCsrfToken: vi.fn(),
    })),
  },
}));

interface MockResponse<T = unknown> extends Omit<AxiosResponse<T>, 'config'> {
  config: InternalAxiosRequestConfig;
}

describe('axios-interceptor', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // Reset document.cookie
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });
  });

  it('should perform a silent refresh on 401 response and retry the original request', async () => {
    let refreshed = false;

    // Keep reference to original adapter to restore later if needed
    const originalAdapter = axios.defaults.adapter as AxiosAdapter;

    // Custom adapter to simulate backend behaviour
    const mockAdapter: AxiosAdapter = async config => {
      // Handle refresh endpoint
      if (config.url === '/api/v1/auth/refresh') {
        refreshed = true;
        const response: MockResponse = {
          status: 200,
          statusText: 'OK',
          data: {},
          headers: {},
          config,
        };
        return Promise.resolve(response);
      }

      // Handle API key list endpoint
      if (
        config.url === '/api/v1/users/me/api-keys' ||
        config.url === '/api/v1/users/me/api-keys/'
      ) {
        if (!refreshed) {
          const error = new Error('Unauthorized') as AxiosError;
          error.config = config;
          error.response = {
            status: 401,
            statusText: 'Unauthorized',
            headers: {},
            data: {},
            config,
          };
          return Promise.reject(error);
        }

        const response: MockResponse = {
          status: 200,
          statusText: 'OK',
          data: { keys: [], total: 0 },
          headers: {},
          config,
        };
        return Promise.resolve(response);
      }

      // Default fallback
      const response: MockResponse = {
        status: 404,
        statusText: 'Not Found',
        data: {},
        headers: {},
        config,
      };
      return Promise.resolve(response);
    };

    // Apply our mock adapter
    axios.defaults.adapter = mockAdapter;

    // Call the service. It should eventually resolve even though the first attempt fails with 401.
    const result = await ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet();

    expect(result).toEqual({ keys: [], total: 0 });
    expect(refreshed).toBe(true);

    // Restore original adapter for safety
    axios.defaults.adapter = originalAdapter;
  });

  it('should update CSRF token in app store after successful refresh', async () => {
    let refreshed = false;
    const mockSetCsrfToken = vi.fn();

    // Mock the app store
    const { useAppStore } = await import('@/stores/useAppStore');
    vi.mocked(useAppStore.getState).mockReturnValue({
      setCsrfToken: mockSetCsrfToken,
    } as unknown as ReturnType<typeof useAppStore.getState>);

    // Mock document.cookie to simulate new CSRF token being set by backend
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrf_token=new-csrf-token-123; access_token=new-access-token',
    });

    // Keep reference to original adapter to restore later if needed
    const originalAdapter = axios.defaults.adapter as AxiosAdapter;

    // Custom adapter to simulate backend behaviour
    const mockAdapter: AxiosAdapter = async config => {
      // Handle refresh endpoint
      if (config.url === '/api/v1/auth/refresh') {
        refreshed = true;
        // Simulate backend setting new CSRF token cookie
        Object.defineProperty(document, 'cookie', {
          writable: true,
          value: 'csrf_token=new-csrf-token-123; access_token=new-access-token',
        });

        const response: MockResponse = {
          status: 200,
          statusText: 'OK',
          data: {},
          headers: {},
          config,
        };
        return Promise.resolve(response);
      }

      // Handle API key list endpoint
      if (
        config.url === '/api/v1/users/me/api-keys' ||
        config.url === '/api/v1/users/me/api-keys/'
      ) {
        if (!refreshed) {
          const error = new Error('Unauthorized') as AxiosError;
          error.config = config;
          error.response = {
            status: 401,
            statusText: 'Unauthorized',
            headers: {},
            data: {},
            config,
          };
          return Promise.reject(error);
        }

        const response: MockResponse = {
          status: 200,
          statusText: 'OK',
          data: { keys: [], total: 0 },
          headers: {},
          config,
        };
        return Promise.resolve(response);
      }

      // Default fallback
      const response: MockResponse = {
        status: 404,
        statusText: 'Not Found',
        data: {},
        headers: {},
        config,
      };
      return Promise.resolve(response);
    };

    // Apply our mock adapter
    axios.defaults.adapter = mockAdapter;

    // Call the service. It should eventually resolve and update CSRF token
    const result = await ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet();

    expect(result).toEqual({ keys: [], total: 0 });
    expect(refreshed).toBe(true);

    // Give the dynamic import time to resolve
    await new Promise(resolve => setTimeout(resolve, 0));

    // Verify that the CSRF token was updated in the app store
    expect(mockSetCsrfToken).toHaveBeenCalledWith('new-csrf-token-123');

    // Restore original adapter for safety
    axios.defaults.adapter = originalAdapter;
  });

  it('should handle CSRF token update errors gracefully', async () => {
    let refreshed = false;
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    // Mock the app store to throw an error
    const { useAppStore } = await import('@/stores/useAppStore');
    vi.mocked(useAppStore.getState).mockImplementation(() => {
      throw new Error('Store error');
    });

    // Keep reference to original adapter to restore later if needed
    const originalAdapter = axios.defaults.adapter as AxiosAdapter;

    // Custom adapter to simulate backend behaviour
    const mockAdapter: AxiosAdapter = async config => {
      // Handle refresh endpoint
      if (config.url === '/api/v1/auth/refresh') {
        refreshed = true;
        const response: MockResponse = {
          status: 200,
          statusText: 'OK',
          data: {},
          headers: {},
          config,
        };
        return Promise.resolve(response);
      }

      // Handle API key list endpoint
      if (
        config.url === '/api/v1/users/me/api-keys' ||
        config.url === '/api/v1/users/me/api-keys/'
      ) {
        if (!refreshed) {
          const error = new Error('Unauthorized') as AxiosError;
          error.config = config;
          error.response = {
            status: 401,
            statusText: 'Unauthorized',
            headers: {},
            data: {},
            config,
          };
          return Promise.reject(error);
        }

        const response: MockResponse = {
          status: 200,
          statusText: 'OK',
          data: { keys: [], total: 0 },
          headers: {},
          config,
        };
        return Promise.resolve(response);
      }

      // Default fallback
      const response: MockResponse = {
        status: 404,
        statusText: 'Not Found',
        data: {},
        headers: {},
        config,
      };
      return Promise.resolve(response);
    };

    // Apply our mock adapter
    axios.defaults.adapter = mockAdapter;

    // Call the service. It should still work even if CSRF token update fails
    const result = await ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet();

    expect(result).toEqual({ keys: [], total: 0 });
    expect(refreshed).toBe(true);

    // Give the dynamic import time to resolve
    await new Promise(resolve => setTimeout(resolve, 0));

    // Verify that the error was logged but didn't break the flow
    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to update app store with CSRF token:',
      expect.any(Error)
    );

    // Restore original adapter for safety
    axios.defaults.adapter = originalAdapter;
    consoleSpy.mockRestore();
  });
});
