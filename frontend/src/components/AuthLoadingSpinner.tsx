import { Box, CircularProgress } from '@mui/material';
import React from 'react';

/**
 * Full-page loading spinner displayed while authentication status is being verified.
 * This prevents the UI from rendering with potentially stale authentication state.
 */
const AuthLoadingSpinner: React.FC = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
      }}
    >
      <CircularProgress />
    </Box>
  );
};

export default AuthLoadingSpinner;
