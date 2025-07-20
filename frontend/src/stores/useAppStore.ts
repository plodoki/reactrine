import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import authService from '../services/authService';
import type { User } from '../types/api';
import { ApiError } from '@/types/api';

interface AppState {
  // Theme state
  themeMode: 'light' | 'dark';

  // Auth state
  user: User | null;
  isAuthenticated: boolean;
  isAuthInitialized: boolean;
  registrationAllowed: boolean;
  registrationMessage: string | null;
  csrfToken: string | null;

  // UI state
  isLoading: boolean;

  // Computed properties for role-based access
  isAdmin: boolean;
  userRole: string | null;

  // Internal state for request deduplication
  _authCheckPromise: Promise<void> | null;

  // Actions
  setThemeMode: (mode: 'light' | 'dark') => void;
  toggleThemeMode: () => void;

  // Auth actions
  login: (email: string, password: string) => Promise<User>;
  loginWithGoogle: (credential: string) => Promise<User>;
  register: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
  checkRegistrationStatus: () => Promise<void>;
  checkAuthStatus: () => Promise<void>;
  setCsrfToken: (token: string | null) => void;

  // UI actions
  setLoading: (loading: boolean) => void;

  // Role helper methods
  hasRole: (role: string) => boolean;
  checkIsAdmin: () => boolean;
  getUserRole: () => string | null;
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        themeMode: 'light',
        user: null,
        isAuthenticated: false,
        isAuthInitialized: false,
        registrationAllowed: true,
        registrationMessage: null,
        csrfToken: null,
        isLoading: false,
        _authCheckPromise: null,

        // Computed properties (getters)
        get isAdmin() {
          const state = get();
          return state.user?.role?.name === 'admin';
        },

        get userRole() {
          const state = get();
          return state.user?.role?.name || null;
        },

        // Theme actions
        setThemeMode: mode => set({ themeMode: mode }),
        toggleThemeMode: () =>
          set(state => ({
            themeMode: state.themeMode === 'light' ? 'dark' : 'light',
          })),

        // Auth actions
        login: async (email: string, password: string) => {
          try {
            set({ isLoading: true });
            const user = await authService.login(email, password);
            set({
              user,
              isAuthenticated: true,
              isAuthInitialized: true, // Mark auth as initialized
              isLoading: false,
            });
            return user;
          } catch (error) {
            set({ isLoading: false });
            throw error;
          }
        },

        loginWithGoogle: async (credential: string) => {
          try {
            set({ isLoading: true });
            const user = await authService.loginWithGoogle(credential);
            set({
              user,
              isAuthenticated: true,
              isAuthInitialized: true, // Mark auth as initialized
              isLoading: false,
            });
            return user;
          } catch (error) {
            set({ isLoading: false });
            throw error;
          }
        },

        register: async (email: string, password: string) => {
          try {
            set({ isLoading: true });
            const user = await authService.register(email, password);
            set({
              user,
              isAuthenticated: true,
              isAuthInitialized: true, // Mark auth as initialized
              isLoading: false,
            });
            return user;
          } catch (error) {
            set({ isLoading: false });
            throw error;
          }
        },

        logout: async () => {
          try {
            await authService.logout();
            set({
              user: null,
              isAuthenticated: false,
              isAuthInitialized: true, // Auth state is known (logged out)
            });
          } catch (error) {
            // Even if logout fails on server, clear local state
            set({
              user: null,
              isAuthenticated: false,
              isAuthInitialized: true, // Auth state is known (logged out)
            });
            console.error('Logout error:', error);
          }
        },

        setUser: user =>
          set({
            user,
            isAuthenticated: !!user,
            isAuthInitialized: true, // User is being set, so auth is initialized
          }),

        checkRegistrationStatus: async () => {
          try {
            const status = await authService.checkRegistrationStatus();
            set({
              registrationAllowed: status.allowed,
              registrationMessage: status.message || null,
            });
          } catch (error) {
            console.error('Failed to check registration status:', error);
          }
        },

        checkAuthStatus: async () => {
          // Check if there's already a pending auth check
          const existingPromise = get()._authCheckPromise;
          if (existingPromise) {
            // Return the existing promise to avoid duplicate requests
            return existingPromise;
          }

          // Create a new auth check promise
          const authCheckPromise = (async () => {
            try {
              const user = await authService.getCurrentUser();
              set({
                user,
                isAuthenticated: true,
              });
            } catch (error) {
              // Only clear auth state for authentication errors (401/403)
              if (ApiError.isApiError(error) && error.response) {
                const status = error.response.status;
                if (status === 401 || status === 403) {
                  // User is not authenticated, clear state
                  set({
                    user: null,
                    isAuthenticated: false,
                  });
                }
              }
              // Don't throw the error - auth check should not fail the flow
            } finally {
              set({ isAuthInitialized: true, _authCheckPromise: null });
            }
          })();

          // Store the promise to prevent duplicate requests
          set({ _authCheckPromise: authCheckPromise });

          return authCheckPromise;
        },

        setCsrfToken: (token: string | null) => set({ csrfToken: token }),

        // UI actions
        setLoading: loading => set({ isLoading: loading }),

        // Role helper methods
        hasRole: (role: string) => {
          const user = get().user;
          return user?.role?.name === role;
        },

        checkIsAdmin: () => {
          const user = get().user;
          return user?.role?.name === 'admin';
        },

        getUserRole: () => {
          const user = get().user;
          return user?.role?.name || null;
        },
      }),
      {
        name: 'app-store', // Storage key
        partialize: state => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
          themeMode: state.themeMode,
          // Don't persist registration status as it's server-side configuration
          // Don't persist CSRF token as it's short-lived
        }),
      }
    ),
    {
      name: 'app-store', // Name for devtools
    }
  )
);

export default useAppStore;
