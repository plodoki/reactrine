import { OpenAPI } from './api-client';

// Configure the generated API client to match our existing API setup
export const configureApiClient = () => {
  // For development, use the Vite proxy. For production, use the environment variable or default to empty string
  // The Vite proxy redirects /api/* to the backend, so we should use an empty base URL
  // This allows the generated client to use relative URLs that work with the proxy
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

  // Set the base URL - empty string means use relative URLs which work with Vite proxy
  OpenAPI.BASE = baseUrl;

  // Enable credentials for session-based auth (same as existing API)
  OpenAPI.WITH_CREDENTIALS = true;
  OpenAPI.CREDENTIALS = 'include';

  // Add CSRF token support through headers resolver
  OpenAPI.HEADERS = async options => {
    const headers: Record<string, string> = {};

    // For state-changing requests (POST, PUT, PATCH, DELETE), add CSRF token
    if (
      options.method &&
      !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase())
    ) {
      try {
        // Get CSRF token from cookie
        const csrfToken = document.cookie
          .split('; ')
          .find(row => row.startsWith('csrf_token='))
          ?.split('=')[1];

        if (csrfToken) {
          headers['X-CSRF-Token'] = csrfToken;
        }
      } catch (error) {
        console.warn('Failed to get CSRF token from cookie:', error);
      }
    }

    return headers;
  };
};

// Initialize the client configuration
configureApiClient();
