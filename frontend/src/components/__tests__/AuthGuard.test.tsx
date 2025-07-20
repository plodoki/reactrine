import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import useAppStore from '../../stores/useAppStore';
import AuthGuard from '../AuthGuard';

// Mock the app store
vi.mock('../../stores/useAppStore', () => ({
  default: vi.fn(),
}));

const mockUseAppStore = vi.mocked(useAppStore);

// Helper component to wrap AuthGuard with MemoryRouter
const AuthGuardWrapper = ({
  children,
  initialEntries = ['/'],
}: {
  children: React.ReactNode;
  initialEntries?: string[];
}) => (
  <MemoryRouter initialEntries={initialEntries}>
    <AuthGuard>{children}</AuthGuard>
  </MemoryRouter>
);

// Default mock return value
const defaultMockStore = {
  isAuthInitialized: false,
  checkAuthStatus: vi.fn(),
  checkRegistrationStatus: vi.fn(),
  user: null,
  isAuthenticated: false,
  registrationAllowed: true,
  registrationMessage: null,
  csrfToken: null,
  isLoading: false,
  themeMode: 'light' as const,
  setThemeMode: vi.fn(),
  toggleThemeMode: vi.fn(),
  login: vi.fn(),
  loginWithGoogle: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  setUser: vi.fn(),
  setCsrfToken: vi.fn(),
  setLoading: vi.fn(),
};

describe('AuthGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAppStore.mockReturnValue(defaultMockStore);
  });

  describe('Public Routes', () => {
    it('should render children for /login route when auth is not initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/login']}>
          <div data-testid="test-child">Login Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('should render children for /register route when auth is not initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/register']}>
          <div data-testid="test-child">Register Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('should render children for /404 route when auth is not initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/404']}>
          <div data-testid="test-child">Not Found Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });

  describe('Unprotected Routes', () => {
    it('should render children for / route when auth is not initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/']}>
          <div data-testid="test-child">Home Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('should render children for /haiku route when auth is not initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/haiku']}>
          <div data-testid="test-child">Haiku Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('should render children for /components route when auth is not initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/components']}>
          <div data-testid="test-child">Components Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('should render children for /settings/llm route when auth is not initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/settings/llm']}>
          <div data-testid="test-child">LLM Settings Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });

  describe('Protected Routes', () => {
    it('should show loading spinner for /profile route when auth is not initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/profile']}>
          <div data-testid="test-child">Profile Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
    });

    it('should show loading spinner for /settings/api-keys route when auth is not initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/settings/api-keys']}>
          <div data-testid="test-child">API Keys Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
    });

    it('should show loading spinner for unknown protected routes when auth is not initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/some/protected/route']}>
          <div data-testid="test-child">Protected Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
    });
  });

  describe('Auth Initialized State', () => {
    it('should render children for all routes when auth is initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: true,
      });

      // Test protected route
      render(
        <AuthGuardWrapper initialEntries={['/profile']}>
          <div data-testid="test-child">Profile Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('should render children for public routes when auth is initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: true,
      });

      render(
        <AuthGuardWrapper initialEntries={['/login']}>
          <div data-testid="test-child">Login Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('should render children for unprotected routes when auth is initialized', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: true,
      });

      render(
        <AuthGuardWrapper initialEntries={['/']}>
          <div data-testid="test-child">Home Page</div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });

  describe('Component Behavior', () => {
    it('should render multiple children when allowed', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/login']}>
          <div data-testid="child-1">Child 1</div>
          <div data-testid="child-2">Child 2</div>
          <span data-testid="child-3">Child 3</span>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('child-1')).toBeInTheDocument();
      expect(screen.getByTestId('child-2')).toBeInTheDocument();
      expect(screen.getByTestId('child-3')).toBeInTheDocument();
    });

    it('should render nested components when allowed', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      render(
        <AuthGuardWrapper initialEntries={['/']}>
          <div data-testid="parent">
            <div data-testid="child">
              <span data-testid="grandchild">Grandchild</span>
            </div>
          </div>
        </AuthGuardWrapper>
      );

      expect(screen.getByTestId('parent')).toBeInTheDocument();
      expect(screen.getByTestId('child')).toBeInTheDocument();
      expect(screen.getByTestId('grandchild')).toBeInTheDocument();
    });

    it('should use useAppStore to get auth state', () => {
      render(
        <AuthGuardWrapper initialEntries={['/']}>
          <div data-testid="test-child">Test Child</div>
        </AuthGuardWrapper>
      );

      expect(mockUseAppStore).toHaveBeenCalled();
    });
  });

  describe('Route Transitions', () => {
    it('should handle different routes correctly', () => {
      mockUseAppStore.mockReturnValue({
        ...defaultMockStore,
        isAuthInitialized: false,
      });

      // Test public route
      const { rerender } = render(
        <AuthGuardWrapper initialEntries={['/login']}>
          <div data-testid="test-child">Content</div>
        </AuthGuardWrapper>
      );

      // Should render children on public route
      expect(screen.getByTestId('test-child')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();

      // Unmount and render with protected route instead
      rerender(
        <div>
          <AuthGuardWrapper initialEntries={['/profile']}>
            <div data-testid="test-child">Content</div>
          </AuthGuardWrapper>
        </div>
      );

      // Should show loading spinner on protected route
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
    });
  });
});
