import { useNotifications } from '@/hooks/useNotifications';
import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import {
  useCreateLlmSettings,
  useLlmSettings,
  useUpdateLlmSettings,
} from './useLlmSettings';

export interface LlmSettingsFormData {
  provider: 'openai' | 'openrouter' | 'bedrock' | 'lmstudio';
  openai_model: string;
  openrouter_model: string;
  bedrock_model: string;
  lmstudio_model: string;
}

const validateLlmSettings = (values: LlmSettingsFormData) => {
  const errors: Partial<Record<keyof LlmSettingsFormData, string>> = {};

  // Validate that the selected provider has a corresponding model
  if (
    values.provider === 'openai' &&
    (!values.openai_model || values.openai_model.trim() === '')
  ) {
    errors.openai_model = 'OpenAI model is required when OpenAI provider is selected';
  }

  if (
    values.provider === 'openrouter' &&
    (!values.openrouter_model || values.openrouter_model.trim() === '')
  ) {
    errors.openrouter_model =
      'OpenRouter model is required when OpenRouter provider is selected';
  }

  if (
    values.provider === 'bedrock' &&
    (!values.bedrock_model || values.bedrock_model.trim() === '')
  ) {
    errors.bedrock_model =
      'Bedrock model is required when Bedrock provider is selected';
  }

  if (
    values.provider === 'lmstudio' &&
    (!values.lmstudio_model || values.lmstudio_model.trim() === '')
  ) {
    errors.lmstudio_model =
      'LMStudio model is required when LMStudio provider is selected';
  }

  return errors;
};

export function useLlmSettingsForm() {
  const { data, isLoading, isError, error: fetchError } = useLlmSettings();
  const updateMutation = useUpdateLlmSettings();
  const createMutation = useCreateLlmSettings();
  const notifications = useNotifications();

  // Create initial values based on loaded data
  const defaultValues = useMemo<LlmSettingsFormData>(
    () => ({
      provider: (data?.provider as LlmSettingsFormData['provider']) || 'openai',
      openai_model: data?.openai_model || '',
      openrouter_model: data?.openrouter_model || '',
      bedrock_model: data?.bedrock_model || '',
      lmstudio_model: data?.lmstudio_model || '',
    }),
    [data]
  );

  const form = useForm<LlmSettingsFormData>({
    defaultValues,
    mode: 'onChange',
  });

  const {
    handleSubmit,
    formState: { isSubmitting, isValid, isDirty },
    reset,
    setError,
  } = form;

  // Reset form when default values change (when data loads)
  useEffect(() => {
    reset(defaultValues);
  }, [defaultValues, reset]);

  const onSubmit = handleSubmit(async values => {
    // Clear any previous errors
    form.clearErrors();

    // Run validation
    const errors = validateLlmSettings(values);
    const hasErrors = Object.keys(errors).length > 0;

    if (hasErrors) {
      Object.entries(errors).forEach(([field, message]) => {
        setError(field as keyof LlmSettingsFormData, {
          type: 'manual',
          message: message as string,
        });
      });
      return;
    }

    try {
      if (data) {
        // Settings exist, update them
        await updateMutation.mutateAsync(values);
      } else {
        // No settings exist, create them
        await createMutation.mutateAsync(values);
      }
      notifications.showSuccessNotification('LLM settings saved successfully!');
    } catch (error) {
      notifications.showErrorNotification(error);
      throw error; // Re-throw to let form handle submission state
    }
  });

  const isPending =
    updateMutation.isPending || createMutation.isPending || isSubmitting;

  return {
    form,
    onSubmit,
    notifications,
    isLoading,
    isError,
    fetchError,
    isPending,
    isUpdate: !!data,
    isValid,
    isDirty,
  };
}
