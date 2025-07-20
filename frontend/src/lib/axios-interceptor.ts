import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import { ApiError } from '@/types/api';

/**
 * Global flag to prevent multiple simultaneous refresh requests.
 */
let isRefreshing = false;

interface FailedQueuePromise {
  resolve: () => void;
  reject: (error: ApiError) => void;
}

let failedQueue: FailedQueuePromise[] = [];

const processQueue = (error: ApiError | null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });

  failedQueue = [];
};

interface CustomAxiosRequestConfig extends AxiosRequestConfig {
  _retry?: boolean;
}

/**
 * Convert AxiosError to our ApiError type
 */
const convertToApiError = (axiosError: AxiosError): ApiError => {
  return new ApiError(axiosError.message, {
    status: axiosError.response?.status || 500,
    statusText: axiosError.response?.statusText || 'Unknown Error',
    data: axiosError.response?.data as ApiError['response']['data'],
  });
};

/**
 * Get CSRF token from cookie
 */
const getCsrfTokenFromCookie = (): string | null => {
  try {
    const csrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_token='))
      ?.split('=')[1];
    return csrfToken || null;
  } catch (error) {
    console.warn('Failed to get CSRF token from cookie:', error);
    return null;
  }
};

/**
 * Update the app store with the new CSRF token if it exists
 */
const updateAppStoreWithCsrfToken = () => {
  try {
    const newCsrfToken = getCsrfTokenFromCookie();

    // Dynamically import the store to avoid circular dependencies
    import('../stores/useAppStore')
      .then(({ useAppStore }) => {
        const { setCsrfToken } = useAppStore.getState();
        setCsrfToken(newCsrfToken);
      })
      .catch(error => {
        console.warn('Failed to update app store with CSRF token:', error);
      });
  } catch (error) {
    console.warn('Failed to update CSRF token in app store:', error);
  }
};

/**
 * Attach a response interceptor to handle 401 responses by attempting to
 * refresh the access token using the backend refresh endpoint. This interceptor
 * is applied to the global axios instance used by the generated API client.
 */
const attach401Interceptor = (client: AxiosInstance) => {
  client.interceptors.response.use(
    response => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as CustomAxiosRequestConfig;

      // Only attempt refresh once per request
      if (error.response?.status === 401 && !originalRequest._retry) {
        if (isRefreshing) {
          // Queue the request until the refresh has resolved
          return new Promise((resolve, reject) => {
            failedQueue.push({
              resolve: () => {
                // After successful refresh, retry the original request
                client(originalRequest).then(resolve).catch(reject);
              },
              reject,
            });
          });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          // Attempt to refresh the session. This sets new cookies on success.
          await axios.post('/api/v1/auth/refresh');

          // Update the app store with the new CSRF token
          // The backend now generates a new CSRF token during refresh
          updateAppStoreWithCsrfToken();

          processQueue(null);

          // Retry the original request with the new session
          return client(originalRequest);
        } catch (err) {
          const axiosError = err as AxiosError;
          const apiError = convertToApiError(axiosError);
          processQueue(apiError);
          // Redirect to login page when refresh fails
          window.location.href = '/login';
          return Promise.reject(apiError);
        } finally {
          isRefreshing = false;
        }
      }

      // Convert axios error to our ApiError type before rejecting
      return Promise.reject(convertToApiError(error));
    }
  );
};

// Apply the interceptor to the global axios instance (used by generated API client)
attach401Interceptor(axios);
