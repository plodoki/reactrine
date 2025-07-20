import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import useAppStore from '../../stores/useAppStore';
import AuthProvider from '../AuthProvider';

// Mock the app store
vi.mock('../../stores/useAppStore', () => ({
  default: vi.fn(),
}));

const mockUseAppStore = vi.mocked(useAppStore);

describe('AuthProvider', () => {
  let mockCheckAuthStatus: ReturnType<typeof vi.fn>;
  let mockCheckRegistrationStatus: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();

    mockCheckAuthStatus = vi.fn();
    mockCheckRegistrationStatus = vi.fn();

    // Mock the store to return our mock functions
    mockUseAppStore.mockReturnValue({
      checkAuthStatus: mockCheckAuthStatus,
      checkRegistrationStatus: mockCheckRegistrationStatus,
      // Add other store properties as needed
      user: null,
      isAuthenticated: false,
      isAuthInitialized: false,
      registrationAllowed: true,
      registrationMessage: null,
      csrfToken: null,
      isLoading: false,
      themeMode: 'light',
      setThemeMode: vi.fn(),
      toggleThemeMode: vi.fn(),
      login: vi.fn(),
      loginWithGoogle: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      setUser: vi.fn(),
      setCsrfToken: vi.fn(),
      setLoading: vi.fn(),
    });

    // Mock console methods to avoid test output
    vi.spyOn(console, 'debug').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should always render children', () => {
      render(
        <AuthProvider>
          <div data-testid="test-child">Test Child</div>
        </AuthProvider>
      );

      // Should always render children since AuthGuard handles loading states
      expect(screen.getByTestId('test-child')).toBeInTheDocument();
    });

    it('should render multiple children', () => {
      render(
        <AuthProvider>
          <div data-testid="child-1">Child 1</div>
          <div data-testid="child-2">Child 2</div>
          <span data-testid="child-3">Child 3</span>
        </AuthProvider>
      );

      expect(screen.getByTestId('child-1')).toBeInTheDocument();
      expect(screen.getByTestId('child-2')).toBeInTheDocument();
      expect(screen.getByTestId('child-3')).toBeInTheDocument();
    });

    it('should render nested components', () => {
      render(
        <AuthProvider>
          <div data-testid="parent">
            <div data-testid="child">
              <span data-testid="grandchild">Grandchild</span>
            </div>
          </div>
        </AuthProvider>
      );

      expect(screen.getByTestId('parent')).toBeInTheDocument();
      expect(screen.getByTestId('child')).toBeInTheDocument();
      expect(screen.getByTestId('grandchild')).toBeInTheDocument();
    });
  });

  describe('Initialization', () => {
    it('should call checkAuthStatus on mount', async () => {
      mockCheckAuthStatus.mockResolvedValue(undefined);
      mockCheckRegistrationStatus.mockResolvedValue(undefined);

      render(
        <AuthProvider>
          <div>Test Child</div>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);
      });
    });

    it('should call checkRegistrationStatus on mount', async () => {
      mockCheckAuthStatus.mockResolvedValue(undefined);
      mockCheckRegistrationStatus.mockResolvedValue(undefined);

      render(
        <AuthProvider>
          <div>Test Child</div>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockCheckRegistrationStatus).toHaveBeenCalledTimes(1);
      });
    });

    it('should initialize both auth and registration status', async () => {
      mockCheckAuthStatus.mockResolvedValue(undefined);
      mockCheckRegistrationStatus.mockResolvedValue(undefined);

      render(
        <AuthProvider>
          <div>Test Child</div>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);
        expect(mockCheckRegistrationStatus).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle checkAuthStatus failure gracefully', async () => {
      const authError = new Error('Auth check failed');
      mockCheckAuthStatus.mockRejectedValue(authError);
      mockCheckRegistrationStatus.mockResolvedValue(undefined);

      render(
        <AuthProvider>
          <div data-testid="test-child">Test Child</div>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);
      });

      // Should render children regardless of auth status
      expect(screen.getByTestId('test-child')).toBeInTheDocument();

      // Should log debug message about user not being authenticated
      expect(console.debug).toHaveBeenCalledWith('User not authenticated on app load');
    });

    it('should handle checkRegistrationStatus failure gracefully', async () => {
      const registrationError = new Error('Registration check failed');
      mockCheckAuthStatus.mockResolvedValue(undefined);
      mockCheckRegistrationStatus.mockRejectedValue(registrationError);

      render(
        <AuthProvider>
          <div data-testid="test-child">Test Child</div>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockCheckRegistrationStatus).toHaveBeenCalledTimes(1);
      });

      // Should render children regardless of registration status
      expect(screen.getByTestId('test-child')).toBeInTheDocument();

      // Should log error message
      expect(console.error).toHaveBeenCalledWith(
        'Failed to check registration status:',
        registrationError
      );
    });

    it('should handle both auth and registration failures gracefully', async () => {
      const authError = new Error('Auth check failed');
      const registrationError = new Error('Registration check failed');
      mockCheckAuthStatus.mockRejectedValue(authError);
      mockCheckRegistrationStatus.mockRejectedValue(registrationError);

      render(
        <AuthProvider>
          <div data-testid="test-child">Test Child</div>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);
        expect(mockCheckRegistrationStatus).toHaveBeenCalledTimes(1);
      });

      // Should render children regardless of errors
      expect(screen.getByTestId('test-child')).toBeInTheDocument();

      // Should log both messages
      expect(console.debug).toHaveBeenCalledWith('User not authenticated on app load');
      expect(console.error).toHaveBeenCalledWith(
        'Failed to check registration status:',
        registrationError
      );
    });
  });

  describe('Store Integration', () => {
    it('should use the correct store functions', () => {
      mockCheckAuthStatus.mockResolvedValue(undefined);
      mockCheckRegistrationStatus.mockResolvedValue(undefined);

      render(
        <AuthProvider>
          <div>Test Child</div>
        </AuthProvider>
      );

      // Verify that the store was called to get the functions
      expect(mockUseAppStore).toHaveBeenCalled();
    });

    it('should call store functions with correct parameters', async () => {
      mockCheckAuthStatus.mockResolvedValue(undefined);
      mockCheckRegistrationStatus.mockResolvedValue(undefined);

      render(
        <AuthProvider>
          <div>Test Child</div>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockCheckAuthStatus).toHaveBeenCalledWith();
        expect(mockCheckRegistrationStatus).toHaveBeenCalledWith();
      });
    });
  });

  describe('Component Lifecycle', () => {
    it('should only initialize once on mount', async () => {
      mockCheckAuthStatus.mockResolvedValue(undefined);
      mockCheckRegistrationStatus.mockResolvedValue(undefined);

      const { rerender } = render(
        <AuthProvider>
          <div>Test Child</div>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);
        expect(mockCheckRegistrationStatus).toHaveBeenCalledTimes(1);
      });

      // Rerender with different children
      rerender(
        <AuthProvider>
          <div>Different Child</div>
        </AuthProvider>
      );

      // Should not call initialization functions again
      expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);
      expect(mockCheckRegistrationStatus).toHaveBeenCalledTimes(1);
    });

    it('should handle unmounting gracefully', async () => {
      mockCheckAuthStatus.mockResolvedValue(undefined);
      mockCheckRegistrationStatus.mockResolvedValue(undefined);

      const { unmount } = render(
        <AuthProvider>
          <div>Test Child</div>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);
      });

      // Should not throw when unmounting
      expect(() => unmount()).not.toThrow();
    });
  });

  describe('Async Behavior', () => {
    it('should handle slow auth check', async () => {
      // Simulate slow auth check
      let resolveAuth: () => void;
      const authPromise = new Promise<void>(resolve => {
        resolveAuth = resolve;
      });
      mockCheckAuthStatus.mockReturnValue(authPromise);
      mockCheckRegistrationStatus.mockResolvedValue(undefined);

      render(
        <AuthProvider>
          <div data-testid="test-child">Test Child</div>
        </AuthProvider>
      );

      // Should render children immediately (AuthGuard handles loading)
      expect(screen.getByTestId('test-child')).toBeInTheDocument();

      // Should have started auth check
      expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);

      // Resolve the auth check
      resolveAuth!();
      await waitFor(() => {
        expect(mockCheckRegistrationStatus).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle slow registration check', async () => {
      // Simulate slow registration check
      let resolveRegistration: () => void;
      const registrationPromise = new Promise<void>(resolve => {
        resolveRegistration = resolve;
      });
      mockCheckAuthStatus.mockResolvedValue(undefined);
      mockCheckRegistrationStatus.mockReturnValue(registrationPromise);

      render(
        <AuthProvider>
          <div data-testid="test-child">Test Child</div>
        </AuthProvider>
      );

      // Should render children immediately (AuthGuard handles loading)
      expect(screen.getByTestId('test-child')).toBeInTheDocument();

      // Should have started both checks
      await waitFor(() => {
        expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);
        expect(mockCheckRegistrationStatus).toHaveBeenCalledTimes(1);
      });

      // Resolve the registration check
      resolveRegistration!();
      await waitFor(() => {
        // Both should be completed
        expect(mockCheckAuthStatus).toHaveBeenCalledTimes(1);
        expect(mockCheckRegistrationStatus).toHaveBeenCalledTimes(1);
      });
    });
  });
});
