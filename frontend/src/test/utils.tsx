import { createTheme, ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, RenderOptions } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';

// Create a simple theme for testing
const testTheme = createTheme();

// Test utilities for consistent testing
// eslint-disable-next-line react-refresh/only-export-components
export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
        gcTime: 0,
      },
    },
  });

export const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <ThemeProvider theme={testTheme}>{children}</ThemeProvider>
    </BrowserRouter>
  </QueryClientProvider>
);

// eslint-disable-next-line react-refresh/only-export-components
export const renderWithProviders = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, { wrapper: TestWrapper, ...options });
};

// Mock error types for testing
export class MockHTTPError extends Error {
  public response: {
    status: number;
    data?: unknown;
  };

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = 'MockHTTPError';
    this.response = { status, data };
  }
}

// Helper to create mock errors with specific status codes
// eslint-disable-next-line react-refresh/only-export-components
export const createMockError = (status: number, message: string, data?: unknown) => {
  return new MockHTTPError(status, message, data);
};

// Mock implementation helpers
// eslint-disable-next-line react-refresh/only-export-components
export const createMockImplementation = (returnValue: unknown) =>
  vi.fn().mockResolvedValue(returnValue);
// eslint-disable-next-line react-refresh/only-export-components
export const createMockRejection = (error: unknown) => vi.fn().mockRejectedValue(error);

// Common test data

export const TEST_USER_EMAIL = 'test@example.com';

export const TEST_USER_PASSWORD = 'password123';

export const TEST_CSRF_TOKEN = 'test-csrf-token';

export const TEST_GOOGLE_CREDENTIAL = 'mock-google-credential';
