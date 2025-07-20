import React from 'react';
import { useLocation } from 'react-router-dom';
import useAppStore from '../stores/useAppStore';
import AuthLoadingSpinner from './AuthLoadingSpinner';

interface Props {
  children: React.ReactNode;
}

// Routes that should be accessible even during auth initialization
const PUBLIC_ROUTES = ['/login', '/register', '/404'];

// Routes that should be accessible without authentication
const UNPROTECTED_ROUTES = ['/', '/haiku', '/components', '/settings/llm'];

/**
 * AuthGuard component that conditionally shows loading spinner based on route and auth status.
 * This component must be used inside a Router context.
 *
 * Logic:
 * - If auth is not initialized AND route is not public/unprotected: show loading spinner
 * - If auth is initialized: allow all routes to render (ProtectedRoute will handle auth checks)
 * - If route is public/unprotected: always allow rendering
 */
const AuthGuard = ({ children }: Props) => {
  const { isAuthInitialized } = useAppStore();
  const location = useLocation();

  // Check if current route should be accessible during auth initialization
  const isPublicRoute = PUBLIC_ROUTES.includes(location.pathname);
  const isUnprotectedRoute = UNPROTECTED_ROUTES.includes(location.pathname);

  // Show loading spinner only if:
  // 1. Auth is not initialized, AND
  // 2. Route is not public (login, register, 404), AND
  // 3. Route is not unprotected (home, haiku, components, llm settings)
  const shouldShowLoading = !isAuthInitialized && !isPublicRoute && !isUnprotectedRoute;

  if (shouldShowLoading) {
    return <AuthLoadingSpinner />;
  }

  return <>{children}</>;
};

export default AuthGuard;
