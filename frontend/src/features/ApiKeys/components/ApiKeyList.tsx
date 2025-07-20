import { type ApiKeyInfo } from '@/lib/api-client';
import {
  DeleteOutline as DeleteIcon,
  KeyOutlined as KeyIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import {
  Box,
  Card,
  CardContent,
  Chip,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
import React from 'react';

interface ApiKeyListProps {
  apiKeys: ApiKeyInfo[];
  onRevoke: (keyId: number) => void;
  isRevoking: boolean;
}

const ApiKeyList: React.FC<ApiKeyListProps> = ({ apiKeys, onRevoke, isRevoking }) => {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusChip = (apiKey: ApiKeyInfo) => {
    if (!apiKey.is_active) {
      return <Chip label="Revoked" color="error" variant="outlined" size="small" />;
    }
    if (apiKey.expires_at && new Date(apiKey.expires_at) < new Date()) {
      return <Chip label="Expired" color="warning" variant="outlined" size="small" />;
    }
    return <Chip label="Active" color="success" variant="outlined" size="small" />;
  };

  const isKeyRevokable = (apiKey: ApiKeyInfo) => {
    return apiKey.is_active;
  };

  if (apiKeys.length === 0) {
    return (
      <Card elevation={2}>
        <CardContent>
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            py={4}
          >
            <KeyIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No API Keys Found
            </Typography>
            <Typography variant="body2" color="text.secondary" textAlign="center">
              You haven't created any API keys yet. Create your first key to get
              started.
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Stack spacing={2}>
      {apiKeys.map(apiKey => (
        <Card key={apiKey.id} elevation={2}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="flex-start">
              <Box flex={1}>
                <Stack direction="row" spacing={2} alignItems="center" mb={1}>
                  <Typography variant="h6">
                    {apiKey.label || `API Key ${apiKey.id}`}
                  </Typography>
                  {getStatusChip(apiKey)}
                </Stack>

                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: {
                      xs: '1fr',
                      sm: '1fr 1fr',
                      md: '1fr 1fr 1fr',
                    },
                    gap: 2,
                    mt: 2,
                  }}
                >
                  <Box>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      display="block"
                    >
                      Key ID
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      #{apiKey.id}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      display="block"
                    >
                      Created
                    </Typography>
                    <Typography variant="body2">
                      {formatDate(apiKey.created_at)}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      display="block"
                    >
                      Last Used
                    </Typography>
                    <Typography variant="body2">
                      {formatDate(apiKey.last_used_at)}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      display="block"
                    >
                      Expires
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography variant="body2">
                        {formatDate(apiKey.expires_at)}
                      </Typography>
                      {apiKey.expires_at &&
                        new Date(apiKey.expires_at) < new Date() && (
                          <Tooltip title="This key has expired">
                            <WarningIcon color="warning" fontSize="small" />
                          </Tooltip>
                        )}
                    </Stack>
                  </Box>
                </Box>
              </Box>

              <Box ml={2}>
                {isKeyRevokable(apiKey) && (
                  <Tooltip title="Revoke API key">
                    <span>
                      <IconButton
                        color="error"
                        onClick={() => onRevoke(apiKey.id)}
                        disabled={isRevoking}
                        size="small"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </span>
                  </Tooltip>
                )}
              </Box>
            </Box>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
};

export default ApiKeyList;
