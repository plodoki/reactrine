import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Alert, Box } from '@mui/material';
import useAppStore from '../stores/useAppStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, roles }) => {
  const { isAuthenticated, user } = useAppStore();
  const location = useLocation();

  if (!isAuthenticated || !user) {
    // Redirect to login page with return url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role-based access
  if (roles && roles.length > 0) {
    const userRole = user?.role?.name;
    if (!userRole || !roles.includes(userRole)) {
      return (
        <Box sx={{ p: 3 }}>
          <Alert severity="error">
            Access denied. You don't have permission to view this page.
          </Alert>
        </Box>
      );
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;
