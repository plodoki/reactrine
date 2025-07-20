import { Add as AddIcon, ContentCopy as CopyIcon } from '@mui/icons-material';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import React, { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { type ApiKeyCreate } from '@/lib/api-client';

interface CreateApiKeyFormProps {
  onSubmit: (data: ApiKeyCreate) => Promise<void>;
  isLoading: boolean;
  lastCreatedToken?: string | null;
  onClose?: () => void;
}

interface FormData {
  label: string;
  expirationDays: string;
}

const EXPIRATION_OPTIONS = [
  { value: '30', label: '30 days' },
  { value: '90', label: '90 days' },
  { value: 'never', label: 'Never expires' },
];

const CreateApiKeyForm: React.FC<CreateApiKeyFormProps> = ({
  onSubmit,
  isLoading,
  lastCreatedToken,
  onClose,
}) => {
  const [showDialog, setShowDialog] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    defaultValues: {
      label: '',
      expirationDays: '90',
    },
  });

  const handleFormSubmit = async (data: FormData) => {
    const request: ApiKeyCreate = {
      label: data.label.trim() || null,
      expires_in_days: null,
    };

    if (data.expirationDays !== 'never') {
      const days = parseInt(data.expirationDays, 10);
      request.expires_in_days = days; // Send days directly to backend
    }

    try {
      await onSubmit(request);
      setShowDialog(true);
      reset();
    } catch (error) {
      // Error handling is done in the parent component
      console.error('Failed to create API key:', error);
    }
  };

  const handleCopyToken = async () => {
    if (lastCreatedToken) {
      try {
        await navigator.clipboard.writeText(lastCreatedToken);
        setCopiedToken(true);
        setTimeout(() => setCopiedToken(false), 2000);
      } catch (error) {
        console.error('Failed to copy token:', error);
      }
    }
  };

  const handleCloseDialog = () => {
    setShowDialog(false);
    setCopiedToken(false);
    if (onClose) {
      onClose();
    }
  };

  return (
    <>
      <Card elevation={2}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Create New API Key
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            API keys allow you to authenticate API requests. Keep your keys secure and
            don't share them publicly.
          </Typography>

          <Box component="form" onSubmit={handleSubmit(handleFormSubmit)}>
            <Stack spacing={3}>
              <TextField
                label="Label (optional)"
                placeholder="e.g., My Mobile App, Production Server"
                fullWidth
                error={!!errors.label}
                helperText={
                  errors.label?.message || 'Give your API key a descriptive name'
                }
                disabled={isLoading || isSubmitting}
                {...register('label', {
                  maxLength: {
                    value: 100,
                    message: 'Label must be 100 characters or less',
                  },
                })}
              />

              <Controller
                name="expirationDays"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel id="expiration-label">Expiration</InputLabel>
                    <Select
                      labelId="expiration-label"
                      value={field.value}
                      label="Expiration"
                      onChange={field.onChange}
                      disabled={isLoading || isSubmitting}
                    >
                      {EXPIRATION_OPTIONS.map(option => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />

              <Button
                type="submit"
                variant="contained"
                startIcon={<AddIcon />}
                disabled={isLoading || isSubmitting}
                size="large"
              >
                {isLoading || isSubmitting ? 'Creating...' : 'Create API Key'}
              </Button>
            </Stack>
          </Box>
        </CardContent>
      </Card>

      {/* Token Display Dialog */}
      <Dialog
        open={showDialog}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { minHeight: 400 },
        }}
      >
        <DialogTitle>
          <Typography variant="h5" component="div">
            API Key Created Successfully!
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3}>
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Important:</strong> This is the only time you'll see this token.
                Make sure to copy it now and store it securely.
              </Typography>
            </Alert>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Your API Key:
              </Typography>
              <Box
                sx={{
                  p: 2,
                  bgcolor: 'grey.100',
                  borderRadius: 1,
                  border: 1,
                  borderColor: 'grey.300',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  wordBreak: 'break-all',
                  position: 'relative',
                }}
              >
                {lastCreatedToken}
                <Tooltip title={copiedToken ? 'Copied!' : 'Copy to clipboard'}>
                  <IconButton
                    onClick={handleCopyToken}
                    size="small"
                    aria-label="Copy to clipboard"
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      bgcolor: 'white',
                      '&:hover': { bgcolor: 'grey.50' },
                    }}
                  >
                    <CopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>

            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Usage Example:
              </Typography>
              <Box
                sx={{
                  p: 2,
                  bgcolor: 'grey.100',
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                }}
              >
                curl -H "Authorization: Bearer {lastCreatedToken?.substring(0, 20)}..."
                https://your-api.com/api/v1/endpoint
              </Box>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} variant="contained" autoFocus>
            I've Saved My Key
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default CreateApiKeyForm;
