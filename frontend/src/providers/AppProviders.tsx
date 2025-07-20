import { ThemeModeProvider } from '@/contexts/ThemeContext';
import { GoogleOAuthProvider } from '@react-oauth/google';
import React from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import AppThemeProvider from './AppThemeProvider';
import AuthProvider from './AuthProvider';
import ReactQueryProvider from './ReactQueryProvider';

interface Props {
  children: React.ReactNode;
}

/**
 * Combined provider component that wraps all application providers.
 * This centralizes provider setup and ensures proper nesting order.
 */
const AppProviders = ({ children }: Props) => {
  const googleClientId = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID || '';
  const isGoogleConfigured =
    googleClientId && googleClientId !== 'your_google_client_id_here';

  return (
    <ErrorBoundary>
      <ReactQueryProvider>
        {isGoogleConfigured ? (
          <GoogleOAuthProvider clientId={googleClientId}>
            <AuthProvider>
              <ThemeModeProvider>
                <AppThemeProvider>{children}</AppThemeProvider>
              </ThemeModeProvider>
            </AuthProvider>
          </GoogleOAuthProvider>
        ) : (
          <AuthProvider>
            <ThemeModeProvider>
              <AppThemeProvider>{children}</AppThemeProvider>
            </ThemeModeProvider>
          </AuthProvider>
        )}
      </ReactQueryProvider>
    </ErrorBoundary>
  );
};

export default AppProviders;
