import { NotificationSnackbars } from '@/components/Notifications';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material';
import { ApiError } from '@/types/api';
import { useEffect } from 'react';
import { Controller } from 'react-hook-form';
import { useLMStudioModels } from './hooks/useLlmSettings';
import { useLlmSettingsForm } from './hooks/useLlmSettingsForm';

const providers = ['openai', 'openrouter', 'bedrock', 'lmstudio'] as const;

const LlmSettingsPage = () => {
  const {
    form,
    onSubmit,
    notifications,
    isLoading,
    isError,
    fetchError,
    isPending,
    isUpdate,
    isDirty,
  } = useLlmSettingsForm();

  const {
    register,
    control,
    watch,
    formState: { errors },
  } = form;

  // Watch the provider field to conditionally fetch LMStudio models
  const selectedProvider = watch('provider');

  const {
    data: lmstudioModels,
    isLoading: isLoadingModels,
    isError: isModelsError,
    refetch: refetchModels,
  } = useLMStudioModels();

  // Fetch LMStudio models when LMStudio provider is selected
  useEffect(() => {
    if (selectedProvider === 'lmstudio') {
      refetchModels();
    }
  }, [selectedProvider, refetchModels]);

  if (isLoading) {
    return (
      <Box sx={{ p: 3, width: '100%' }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      </Box>
    );
  }

  // Error handling
  if (isError && fetchError) {
    let errorMessage = 'Failed to load LLM settings. Please try refreshing the page.';

    if (ApiError.isApiError(fetchError)) {
      const status = fetchError.response?.status;
      if (status === 401) {
        errorMessage = 'Authentication required. Please log in to view LLM settings.';
      } else if (status === 403) {
        errorMessage =
          'Access denied. You do not have permission to view LLM settings.';
      } else if (status === 404) {
        errorMessage = 'No LLM settings found. You can create new settings below.';
      }
    }

    return (
      <Box sx={{ p: 3, width: '100%' }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {errorMessage}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, width: '100%' }}>
      <Typography variant="h4" sx={{ my: 2 }}>
        LLM Settings
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Controller
          name="provider"
          control={control}
          rules={{ required: 'Provider is required' }}
          render={({ field }) => (
            <FormControl fullWidth error={!!errors.provider}>
              <InputLabel id="provider-label">Provider</InputLabel>
              <Select
                labelId="provider-label"
                value={field.value}
                label="Provider"
                onChange={field.onChange}
                disabled={isPending}
              >
                {providers.map(p => (
                  <MenuItem key={p} value={p}>
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        />

        <TextField
          label="OpenAI Model"
          placeholder="e.g., gpt-4o-mini"
          disabled={isPending}
          error={!!errors.openai_model}
          helperText={errors.openai_model?.message}
          {...register('openai_model')}
        />

        <TextField
          label="OpenRouter Model"
          placeholder="e.g., google/gemini-2.5-flash"
          disabled={isPending}
          error={!!errors.openrouter_model}
          helperText={errors.openrouter_model?.message}
          {...register('openrouter_model')}
        />

        <TextField
          label="Bedrock Model"
          placeholder="e.g., us.anthropic.claude-3-5-sonnet-20241022-v2:0"
          disabled={isPending}
          error={!!errors.bedrock_model}
          helperText={errors.bedrock_model?.message}
          {...register('bedrock_model')}
        />

        {selectedProvider === 'lmstudio' ? (
          <Controller
            name="lmstudio_model"
            control={control}
            rules={{
              required: 'LMStudio model is required when LMStudio provider is selected',
            }}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.lmstudio_model}>
                <InputLabel id="lmstudio-model-label">LMStudio Model</InputLabel>
                <Select
                  labelId="lmstudio-model-label"
                  value={field.value}
                  label="LMStudio Model"
                  onChange={field.onChange}
                  disabled={isPending || isLoadingModels}
                  startAdornment={
                    isLoadingModels ? <CircularProgress size={20} /> : null
                  }
                >
                  {isModelsError ? (
                    <MenuItem disabled>
                      <em>Error loading models</em>
                    </MenuItem>
                  ) : lmstudioModels && lmstudioModels.length > 0 ? (
                    lmstudioModels.map((model: string) => (
                      <MenuItem key={model} value={model}>
                        {model}
                      </MenuItem>
                    ))
                  ) : (
                    <MenuItem disabled>
                      <em>No models available</em>
                    </MenuItem>
                  )}
                </Select>
                {errors.lmstudio_model && (
                  <Typography variant="caption" color="error" sx={{ mt: 1 }}>
                    {errors.lmstudio_model.message}
                  </Typography>
                )}
              </FormControl>
            )}
          />
        ) : (
          <TextField
            label="LMStudio Model"
            placeholder="e.g., llama-3.2-3b-instruct"
            disabled={isPending}
            error={!!errors.lmstudio_model}
            helperText={errors.lmstudio_model?.message}
            {...register('lmstudio_model')}
          />
        )}

        <Button
          variant="contained"
          onClick={onSubmit}
          disabled={isPending || !isDirty}
          startIcon={isPending ? <CircularProgress size={20} /> : null}
        >
          {isPending ? 'Saving...' : isUpdate ? 'Update Settings' : 'Create Settings'}
        </Button>
      </Box>

      <NotificationSnackbars
        showSuccess={notifications.showSuccess}
        showError={notifications.showError}
        successMessage={notifications.successMessage}
        errorMessage={notifications.errorMessage}
        onCloseSuccess={notifications.hideSuccess}
        onCloseError={notifications.hideError}
      />
    </Box>
  );
};

export default LlmSettingsPage;
