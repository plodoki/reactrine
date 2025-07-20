import { NotificationSnackbars } from '@/components/Notifications';
import { type ApiKeyCreate } from '@/lib/api-client';
import { Security as SecurityIcon } from '@mui/icons-material';
import {
  Alert,
  Box,
  CircularProgress,
  Container,
  Divider,
  Stack,
  Typography,
} from '@mui/material';
import React, { useState } from 'react';
import { ApiError } from '@/types/api';
import ApiKeyList from './components/ApiKeyList';
import CreateApiKeyForm from './components/CreateApiKeyForm';
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from './hooks/useApiKeys';

const ApiKeysPage: React.FC = () => {
  const [lastCreatedToken, setLastCreatedToken] = useState<string | null>(null);

  const { data: apiKeys = [], isLoading, isError, error: fetchError } = useApiKeys();

  const createMutation = useCreateApiKey();
  const revokeMutation = useRevokeApiKey();

  const handleCreateApiKey = async (request: ApiKeyCreate) => {
    try {
      const response = await createMutation.mutateAsync(request);
      setLastCreatedToken(response.token);
    } catch (error) {
      console.error('Failed to create API key:', error);
      throw error; // Re-throw to let the form handle it
    }
  };

  const handleRevokeApiKey = async (keyId: number) => {
    try {
      await revokeMutation.mutateAsync(keyId);
    } catch (error) {
      console.error('Failed to revoke API key:', error);
    }
  };

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="50vh"
        >
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  // Error message helper function
  const getErrorMessage = (error: unknown) => {
    if (ApiError.isApiError(error)) {
      if (error.response?.status === 401) {
        return 'Authentication required. Please log in to view your API keys.';
      }
      if (error.response?.status === 403) {
        return 'Access denied. You do not have permission to view API keys.';
      }
    }
    return 'Failed to load API keys. Please try refreshing the page.';
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Stack spacing={3}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SecurityIcon fontSize="large" color="primary" />
          <Typography variant="h4" component="h1">
            API Keys
          </Typography>
        </Box>

        {/* Error Alert */}
        {isError && <Alert severity="error">{getErrorMessage(fetchError)}</Alert>}

        {/* Security Notice */}
        <Alert severity="info">
          <Typography variant="body2">
            <strong>Security Notice:</strong> API keys provide full access to your
            account. Keep them secure, don't share them publicly, and revoke any keys
            you no longer need. Never commit API keys to version control systems.
          </Typography>
        </Alert>

        {/* Create API Key Form */}
        <CreateApiKeyForm
          onSubmit={handleCreateApiKey}
          isLoading={createMutation.isPending}
          lastCreatedToken={lastCreatedToken}
          onClose={() => setLastCreatedToken(null)}
        />

        <Divider />

        {/* API Keys List */}
        <Box>
          <Typography variant="h5" gutterBottom>
            Your API Keys
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            {apiKeys.length === 0
              ? 'You have no API keys yet.'
              : `You have ${apiKeys.length} API key${apiKeys.length !== 1 ? 's' : ''}.`}
          </Typography>

          <ApiKeyList
            apiKeys={apiKeys}
            onRevoke={handleRevokeApiKey}
            isRevoking={revokeMutation.isPending}
          />
        </Box>
      </Stack>

      {/* Notifications */}
      <NotificationSnackbars
        showSuccess={false}
        showError={false}
        successMessage=""
        errorMessage=""
        onCloseSuccess={() => {}}
        onCloseError={() => {}}
      />
    </Container>
  );
};

export default ApiKeysPage;
