import React, { useEffect } from 'react';
import useAppStore from '../stores/useAppStore';

interface Props {
  children: React.ReactNode;
}

/**
 * Authentication provider that initializes auth state on app load.
 * Checks current authentication status and registration availability.
 * The AuthGuard component handles showing loading spinners based on routes.
 */
const AuthProvider = ({ children }: Props) => {
  const { checkAuthStatus, checkRegistrationStatus } = useAppStore();

  useEffect(() => {
    // Initialize auth state and registration status on app load
    const initializeAuth = async () => {
      try {
        // Check if user is already authenticated (via cookies)
        await checkAuthStatus();
      } catch {
        // User is not authenticated, which is fine
        console.debug('User not authenticated on app load');
      }

      try {
        // Check registration status
        await checkRegistrationStatus();
      } catch (error) {
        console.error('Failed to check registration status:', error);
      }
    };

    initializeAuth();
  }, [checkAuthStatus, checkRegistrationStatus]);

  // Always render children - AuthGuard will handle loading states
  return <>{children}</>;
};

export default AuthProvider;
