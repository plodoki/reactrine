import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import useAppStore from '../useAppStore';
import { ApiError, User } from '@/types/api';

// Helper function to create test users with proper typing
const createTestUser = (overrides: Partial<User> = {}): User => ({
  id: 1,
  email: 'test@example.com',
  auth_provider: 'email',
  is_active: true,
  role: { name: 'user', description: 'Regular user' },
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  ...overrides,
});

// Mock the auth service using vi.hoisted to avoid hoisting issues
const mockAuthService = vi.hoisted(() => ({
  login: vi.fn(),
  loginWithGoogle: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn(),
  checkRegistrationStatus: vi.fn(),
}));

vi.mock('../../services/authService', () => ({
  default: mockAuthService,
}));

describe('useAppStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state before each test
    useAppStore.setState({
      themeMode: 'light',
      user: null,
      isAuthenticated: false,
      registrationAllowed: true,
      registrationMessage: null,
      csrfToken: null,
      isLoading: false,
    });
  });

  describe('Theme Management', () => {
    it('should have initial theme mode as light', () => {
      const { result } = renderHook(() => useAppStore());
      expect(result.current.themeMode).toBe('light');
    });

    it('should set theme mode', () => {
      const { result } = renderHook(() => useAppStore());

      act(() => {
        result.current.setThemeMode('dark');
      });

      expect(result.current.themeMode).toBe('dark');
    });

    it('should toggle theme mode from light to dark', () => {
      const { result } = renderHook(() => useAppStore());

      act(() => {
        result.current.toggleThemeMode();
      });

      expect(result.current.themeMode).toBe('dark');
    });

    it('should toggle theme mode from dark to light', () => {
      const { result } = renderHook(() => useAppStore());

      // First set to dark
      act(() => {
        result.current.setThemeMode('dark');
      });

      // Then toggle
      act(() => {
        result.current.toggleThemeMode();
      });

      expect(result.current.themeMode).toBe('light');
    });
  });

  describe('Authentication State Management', () => {
    it('should have initial authentication state', () => {
      const { result } = renderHook(() => useAppStore());

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.registrationAllowed).toBe(true);
      expect(result.current.registrationMessage).toBeNull();
      expect(result.current.csrfToken).toBeNull();
    });

    it('should set user and authentication state', () => {
      const { result } = renderHook(() => useAppStore());
      const testUser = createTestUser();

      act(() => {
        result.current.setUser(testUser);
      });

      expect(result.current.user).toEqual(testUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should clear user and authentication state when user is null', () => {
      const { result } = renderHook(() => useAppStore());
      const testUser = createTestUser();

      // First set user
      act(() => {
        result.current.setUser(testUser);
      });

      // Then clear user
      act(() => {
        result.current.setUser(null);
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should set CSRF token', () => {
      const { result } = renderHook(() => useAppStore());
      const testToken = 'test-csrf-token';

      act(() => {
        result.current.setCsrfToken(testToken);
      });

      expect(result.current.csrfToken).toBe(testToken);
    });

    it('should clear CSRF token', () => {
      const { result } = renderHook(() => useAppStore());

      // First set token
      act(() => {
        result.current.setCsrfToken('test-token');
      });

      // Then clear token
      act(() => {
        result.current.setCsrfToken(null);
      });

      expect(result.current.csrfToken).toBeNull();
    });
  });

  describe('UI State Management', () => {
    it('should have initial loading state as false', () => {
      const { result } = renderHook(() => useAppStore());
      expect(result.current.isLoading).toBe(false);
    });

    it('should set loading state', () => {
      const { result } = renderHook(() => useAppStore());

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.isLoading).toBe(true);
    });

    it('should clear loading state', () => {
      const { result } = renderHook(() => useAppStore());

      // First set loading
      act(() => {
        result.current.setLoading(true);
      });

      // Then clear loading
      act(() => {
        result.current.setLoading(false);
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Async Actions', () => {
    it('should login successfully', async () => {
      const { result } = renderHook(() => useAppStore());
      const testUser = createTestUser();
      const email = 'test@example.com';
      const password = 'password123';

      mockAuthService.login.mockResolvedValue(testUser);

      await act(async () => {
        await result.current.login(email, password);
      });

      expect(mockAuthService.login).toHaveBeenCalledWith(email, password);
      expect(result.current.user).toEqual(testUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle login failure', async () => {
      const { result } = renderHook(() => useAppStore());
      const email = 'test@example.com';
      const password = 'wrongpassword';
      const error = new ApiError('Invalid credentials', {
        status: 401,
        statusText: 'Unauthorized',
      });

      mockAuthService.login.mockRejectedValue(error);

      await expect(async () => {
        await act(async () => {
          await result.current.login(email, password);
        });
      }).rejects.toThrow('Invalid credentials');

      expect(mockAuthService.login).toHaveBeenCalledWith(email, password);
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    it('should login with Google successfully', async () => {
      const { result } = renderHook(() => useAppStore());
      const testUser = createTestUser({ auth_provider: 'google' });
      const credential = 'google-credential-token';

      mockAuthService.loginWithGoogle.mockResolvedValue(testUser);

      await act(async () => {
        await result.current.loginWithGoogle(credential);
      });

      expect(mockAuthService.loginWithGoogle).toHaveBeenCalledWith(credential);
      expect(result.current.user).toEqual(testUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle Google login failure', async () => {
      const { result } = renderHook(() => useAppStore());
      const credential = 'invalid-google-credential';
      const error = new ApiError('Invalid Google credential', {
        status: 401,
        statusText: 'Unauthorized',
      });

      mockAuthService.loginWithGoogle.mockRejectedValue(error);

      await expect(async () => {
        await act(async () => {
          await result.current.loginWithGoogle(credential);
        });
      }).rejects.toThrow('Invalid Google credential');

      expect(mockAuthService.loginWithGoogle).toHaveBeenCalledWith(credential);
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    it('should register successfully', async () => {
      const { result } = renderHook(() => useAppStore());
      const testUser = createTestUser({ email: 'newuser@example.com' });
      const email = 'newuser@example.com';
      const password = 'password123';

      mockAuthService.register.mockResolvedValue(testUser);

      await act(async () => {
        await result.current.register(email, password);
      });

      expect(mockAuthService.register).toHaveBeenCalledWith(email, password);
      expect(result.current.user).toEqual(testUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle registration failure', async () => {
      const { result } = renderHook(() => useAppStore());
      const email = 'existing@example.com';
      const password = 'password123';
      const error = new ApiError('User already exists', {
        status: 400,
        statusText: 'Bad Request',
      });

      mockAuthService.register.mockRejectedValue(error);

      await expect(async () => {
        await act(async () => {
          await result.current.register(email, password);
        });
      }).rejects.toThrow('User already exists');

      expect(mockAuthService.register).toHaveBeenCalledWith(email, password);
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    it('should logout successfully', async () => {
      const { result } = renderHook(() => useAppStore());
      const testUser = createTestUser();

      // First set user
      act(() => {
        result.current.setUser(testUser);
      });

      mockAuthService.logout.mockResolvedValue(undefined);

      await act(async () => {
        await result.current.logout();
      });

      expect(mockAuthService.logout).toHaveBeenCalled();
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should clear local state even if logout fails', async () => {
      const { result } = renderHook(() => useAppStore());
      const testUser = createTestUser();

      // First set user
      act(() => {
        result.current.setUser(testUser);
      });

      const error = new ApiError('Logout failed', {
        status: 500,
        statusText: 'Internal Server Error',
      });
      mockAuthService.logout.mockRejectedValue(error);

      // Mock console.error to avoid test output
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await act(async () => {
        await result.current.logout();
      });

      expect(mockAuthService.logout).toHaveBeenCalled();
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(consoleSpy).toHaveBeenCalledWith('Logout error:', error);

      consoleSpy.mockRestore();
    });

    it('should check registration status successfully', async () => {
      const { result } = renderHook(() => useAppStore());
      const status = {
        allowed: false,
        message: 'Registration is currently disabled',
      };

      mockAuthService.checkRegistrationStatus.mockResolvedValue(status);

      await act(async () => {
        await result.current.checkRegistrationStatus();
      });

      expect(mockAuthService.checkRegistrationStatus).toHaveBeenCalled();
      expect(result.current.registrationAllowed).toBe(false);
      expect(result.current.registrationMessage).toBe(
        'Registration is currently disabled'
      );
    });

    it('should handle registration status with null message', async () => {
      const { result } = renderHook(() => useAppStore());
      const status = {
        allowed: true,
        message: undefined,
      };

      mockAuthService.checkRegistrationStatus.mockResolvedValue(status);

      await act(async () => {
        await result.current.checkRegistrationStatus();
      });

      expect(result.current.registrationAllowed).toBe(true);
      expect(result.current.registrationMessage).toBeNull();
    });

    it('should handle registration status check failure', async () => {
      const { result } = renderHook(() => useAppStore());
      const error = new ApiError('Failed to check registration status', {
        status: 500,
        statusText: 'Internal Server Error',
      });

      mockAuthService.checkRegistrationStatus.mockRejectedValue(error);

      // Mock console.error to avoid test output
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await act(async () => {
        await result.current.checkRegistrationStatus();
      });

      expect(mockAuthService.checkRegistrationStatus).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to check registration status:',
        error
      );

      consoleSpy.mockRestore();
    });

    it('should check auth status successfully', async () => {
      const { result } = renderHook(() => useAppStore());
      const testUser = createTestUser();

      mockAuthService.getCurrentUser.mockResolvedValue(testUser);

      await act(async () => {
        await result.current.checkAuthStatus();
      });

      expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
      expect(result.current.user).toEqual(testUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should handle non-auth HTTP errors without throwing', async () => {
      const { result } = renderHook(() => useAppStore());
      const error = new ApiError('Server error', {
        status: 500,
        statusText: 'Internal Server Error',
      });
      mockAuthService.getCurrentUser.mockRejectedValue(error);

      await act(async () => {
        await result.current.checkAuthStatus();
      });

      // Auth should be marked as initialized even with server errors
      expect(result.current.isAuthInitialized).toBe(true);
      expect(result.current.isAuthenticated).toBe(false);
      expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
    });

    it('should handle non-HTTP errors without throwing', async () => {
      const { result } = renderHook(() => useAppStore());
      const error = new Error('Network error');
      mockAuthService.getCurrentUser.mockRejectedValue(error);

      await act(async () => {
        await result.current.checkAuthStatus();
      });

      // Auth should be marked as initialized even with network errors
      expect(result.current.isAuthInitialized).toBe(true);
      expect(result.current.isAuthenticated).toBe(false);
      expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
    });
  });

  describe('Store Persistence', () => {
    it('should persist specific state properties', () => {
      const { result } = renderHook(() => useAppStore());
      const testUser = createTestUser();

      act(() => {
        result.current.setUser(testUser);
        result.current.setThemeMode('dark');
        result.current.setCsrfToken('test-token');
      });

      // The persistence is handled by Zustand middleware
      // We can verify the state is set correctly
      expect(result.current.user).toEqual(testUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.themeMode).toBe('dark');
      // CSRF token should not be persisted (excluded in partialize)
      expect(result.current.csrfToken).toBe('test-token');
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined registration message', async () => {
      const { result } = renderHook(() => useAppStore());
      const status = {
        allowed: true,
        // message is undefined
      };

      mockAuthService.checkRegistrationStatus.mockResolvedValue(status);

      await act(async () => {
        await result.current.checkRegistrationStatus();
      });

      expect(result.current.registrationAllowed).toBe(true);
      expect(result.current.registrationMessage).toBeNull();
    });

    it('should handle network error without response', async () => {
      const { result } = renderHook(() => useAppStore());
      const error = new Error('Network error');
      mockAuthService.getCurrentUser.mockRejectedValue(error);

      await act(async () => {
        await result.current.checkAuthStatus();
      });

      // Auth should be marked as initialized even if there's an error
      expect(result.current.isAuthInitialized).toBe(true);
      expect(result.current.isAuthenticated).toBe(false);
    });
  });
});
