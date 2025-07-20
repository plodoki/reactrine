import { renderWithProviders } from '@/test/utils';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ApiError } from '@/types/api';
import { JSX } from 'react';
import { describe, expect, it, vi } from 'vitest';
import LlmSettingsPage from '../LlmSettingsPage';

// Types for React Hook Form Controller
interface ControllerRenderProps {
  field: {
    value: string;
    onChange: (value: string) => void;
    onBlur: () => void;
    name: string;
    ref: (ref: unknown) => void;
  };
  fieldState: {
    invalid: boolean;
    isTouched: boolean;
    isDirty: boolean;
    error?: unknown;
  };
  formState: {
    errors: Record<string, unknown>;
    isValid: boolean;
    isDirty: boolean;
    isSubmitting: boolean;
  };
}

// Mock React Hook Form components
let mockProviderValue = 'openai';
let mockLMStudioModelValue = '';

vi.mock('react-hook-form', () => ({
  Controller: ({
    render,
    name,
  }: {
    render: (props: ControllerRenderProps) => JSX.Element;
    name: string;
  }) => {
    // Return appropriate default values based on the field name
    const getFieldValue = (fieldName: string) => {
      switch (fieldName) {
        case 'provider':
          return mockProviderValue;
        case 'openai_model':
          return 'gpt-4o-mini';
        case 'openrouter_model':
          return 'google/gemini-2.5-flash';
        case 'bedrock_model':
          return 'us.anthropic.claude-3-5-sonnet-20241022-v2:0';
        case 'lmstudio_model':
          return mockLMStudioModelValue;
        default:
          return '';
      }
    };

    const fieldProps = {
      field: {
        value: getFieldValue(name),
        onChange: vi.fn(),
        onBlur: vi.fn(),
        name,
        ref: vi.fn(),
      },
      fieldState: {
        invalid: false,
        isTouched: false,
        isDirty: false,
        error: undefined,
      },
      formState: {
        errors: {},
        isValid: true,
        isDirty: false,
        isSubmitting: false,
      },
    };
    return render(fieldProps);
  },
}));

// Mock the hooks
vi.mock('../hooks/useLlmSettingsForm', () => ({
  useLlmSettingsForm: vi.fn(),
}));

vi.mock('../hooks/useLlmSettings', () => ({
  useLMStudioModels: vi.fn(),
}));

import { useLMStudioModels } from '../hooks/useLlmSettings';
import { useLlmSettingsForm } from '../hooks/useLlmSettingsForm';

describe('LlmSettingsPage Component', () => {
  const mockUseLlmSettingsForm = useLlmSettingsForm as ReturnType<typeof vi.fn>;
  const mockUseLMStudioModels = useLMStudioModels as ReturnType<typeof vi.fn>;

  const defaultFormHook = {
    form: {
      register: vi.fn(() => ({})),
      control: {},
      watch: vi.fn((name?: string) => {
        if (name === 'provider') return 'openai';
        return '';
      }),
      formState: { errors: {} },
      handleSubmit: vi.fn(),
      clearErrors: vi.fn(),
      setError: vi.fn(),
      reset: vi.fn(),
    },
    onSubmit: vi.fn(),
    notifications: {
      showSuccess: false,
      showError: false,
      successMessage: '',
      errorMessage: '',
      hideSuccess: vi.fn(),
      hideError: vi.fn(),
    },
    isLoading: false,
    isError: false,
    fetchError: null,
    isPending: false,
    isUpdate: false,
    isDirty: false,
    isValid: true,
  };

  const defaultModelsHook = {
    data: [],
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseLlmSettingsForm.mockReturnValue(defaultFormHook);
    mockUseLMStudioModels.mockReturnValue(defaultModelsHook);

    // Reset mock values
    mockProviderValue = 'openai';
    mockLMStudioModelValue = '';
  });

  describe('Loading State', () => {
    it('should show loading spinner when isLoading is true', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isLoading: true,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.queryByText('LLM Settings')).not.toBeInTheDocument();
    });
  });

  describe('Form Rendering', () => {
    it('should render all form fields', () => {
      renderWithProviders(<LlmSettingsPage />);

      expect(screen.getByText('LLM Settings')).toBeInTheDocument();
      expect(screen.getByLabelText(/provider/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/openai model/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/openrouter model/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/bedrock model/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/lmstudio model/i)).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /create settings/i })
      ).toBeInTheDocument();
    });

    it('should show all provider options', async () => {
      const user = userEvent.setup();
      renderWithProviders(<LlmSettingsPage />);

      const providerSelect = screen.getByLabelText(/provider/i);
      await user.click(providerSelect);

      // Use getAllByText to handle multiple instances and check for options specifically
      const openaiOptions = screen.getAllByText('Openai');
      expect(openaiOptions.length).toBeGreaterThan(0);

      expect(screen.getByText('Openrouter')).toBeInTheDocument();
      expect(screen.getByText('Bedrock')).toBeInTheDocument();
      expect(screen.getByText('Lmstudio')).toBeInTheDocument();
    });

    it('should show placeholders for model fields', () => {
      renderWithProviders(<LlmSettingsPage />);

      expect(screen.getByPlaceholderText('e.g., gpt-4o-mini')).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText('e.g., google/gemini-2.5-flash')
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(
          'e.g., us.anthropic.claude-3-5-sonnet-20241022-v2:0'
        )
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText('e.g., llama-3.2-3b-instruct')
      ).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should show authentication error message', () => {
      // Create a proper ApiError instance
      const mockError = new ApiError('Request failed with status code 401', {
        status: 401,
        statusText: 'Unauthorized',
        data: {},
      });

      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isError: true,
        fetchError: mockError,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(
        screen.getByText('Authentication required. Please log in to view LLM settings.')
      ).toBeInTheDocument();
    });

    it('should show access denied error message', () => {
      // Create a proper ApiError instance
      const mockError = new ApiError('Request failed with status code 403', {
        status: 403,
        statusText: 'Forbidden',
        data: {},
      });

      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isError: true,
        fetchError: mockError,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(
        screen.getByText(
          'Access denied. You do not have permission to view LLM settings.'
        )
      ).toBeInTheDocument();
    });

    it('should show not found error message', () => {
      // Create a proper ApiError instance
      const mockError = new ApiError('Request failed with status code 404', {
        status: 404,
        statusText: 'Not Found',
        data: {},
      });

      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isError: true,
        fetchError: mockError,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(
        screen.getByText('No LLM settings found. You can create new settings below.')
      ).toBeInTheDocument();
    });

    it('should show generic error message for other errors', () => {
      const mockError = {
        response: { status: 500 },
        isAxiosError: true,
      };

      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isError: true,
        fetchError: mockError,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(
        screen.getByText('Failed to load LLM settings. Please try refreshing the page.')
      ).toBeInTheDocument();
    });

    it('should show generic error message for non-axios errors', () => {
      const mockError = new Error('Network error');

      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isError: true,
        fetchError: mockError,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(
        screen.getByText('Failed to load LLM settings. Please try refreshing the page.')
      ).toBeInTheDocument();
    });
  });

  describe('LMStudio Provider Handling', () => {
    it('should show LMStudio model dropdown when LMStudio provider is selected', () => {
      mockProviderValue = 'lmstudio';
      const mockWatch = vi.fn().mockReturnValue('lmstudio');
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          ...defaultFormHook.form,
          watch: mockWatch,
        },
      });

      mockUseLMStudioModels.mockReturnValue({
        ...defaultModelsHook,
        data: ['model1', 'model2'],
      });

      renderWithProviders(<LlmSettingsPage />);

      // Should show dropdown instead of text field
      expect(screen.getByLabelText(/lmstudio model/i)).toBeInTheDocument();
      expect(
        screen.queryByPlaceholderText('e.g., llama-3.2-3b-instruct')
      ).not.toBeInTheDocument();
    });

    it('should show loading state in LMStudio model dropdown', () => {
      mockProviderValue = 'lmstudio';
      const mockWatch = vi.fn().mockReturnValue('lmstudio');
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          ...defaultFormHook.form,
          watch: mockWatch,
        },
      });

      mockUseLMStudioModels.mockReturnValue({
        ...defaultModelsHook,
        isLoading: true,
      });

      renderWithProviders(<LlmSettingsPage />);

      // Should show loading spinner in select
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should show error state in LMStudio model dropdown', async () => {
      mockProviderValue = 'lmstudio';
      const user = userEvent.setup();
      const mockWatch = vi.fn().mockReturnValue('lmstudio');
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          ...defaultFormHook.form,
          watch: mockWatch,
        },
      });

      mockUseLMStudioModels.mockReturnValue({
        ...defaultModelsHook,
        isError: true,
      });

      renderWithProviders(<LlmSettingsPage />);

      const select = screen.getByLabelText(/lmstudio model/i);
      await user.click(select);

      expect(screen.getByText('Error loading models')).toBeInTheDocument();
    });

    it('should show no models available message', async () => {
      mockProviderValue = 'lmstudio';
      const user = userEvent.setup();
      const mockWatch = vi.fn().mockReturnValue('lmstudio');
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          ...defaultFormHook.form,
          watch: mockWatch,
        },
      });

      mockUseLMStudioModels.mockReturnValue({
        ...defaultModelsHook,
        data: [],
      });

      renderWithProviders(<LlmSettingsPage />);

      const select = screen.getByLabelText(/lmstudio model/i);
      await user.click(select);

      expect(screen.getByText('No models available')).toBeInTheDocument();
    });

    it('should show available models in dropdown', async () => {
      mockProviderValue = 'lmstudio';
      mockLMStudioModelValue = 'model1';
      const user = userEvent.setup();
      const mockWatch = vi.fn().mockReturnValue('lmstudio');
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          ...defaultFormHook.form,
          watch: mockWatch,
        },
      });

      mockUseLMStudioModels.mockReturnValue({
        ...defaultModelsHook,
        data: ['model1', 'model2', 'model3'],
      });

      renderWithProviders(<LlmSettingsPage />);

      const select = screen.getByLabelText(/lmstudio model/i);
      await user.click(select);

      // Use getAllByText to handle multiple instances of the same text
      const model1Options = screen.getAllByText('model1');
      expect(model1Options.length).toBeGreaterThan(0);
      expect(screen.getByText('model2')).toBeInTheDocument();
      expect(screen.getByText('model3')).toBeInTheDocument();
    });

    it('should call refetch when LMStudio provider is selected', () => {
      mockProviderValue = 'lmstudio';
      const mockRefetch = vi.fn();
      const mockWatch = vi.fn().mockReturnValue('lmstudio');

      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          ...defaultFormHook.form,
          watch: mockWatch,
        },
      });

      mockUseLMStudioModels.mockReturnValue({
        ...defaultModelsHook,
        refetch: mockRefetch,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Form States', () => {
    it('should disable form fields when pending', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isPending: true,
      });

      renderWithProviders(<LlmSettingsPage />);

      // For Material-UI Select components, check aria-disabled attribute
      const providerSelect = screen.getByLabelText(/provider/i);
      expect(providerSelect).toHaveAttribute('aria-disabled', 'true');

      // For regular TextField components, check disabled attribute
      expect(screen.getByLabelText(/openai model/i)).toBeDisabled();
      expect(screen.getByLabelText(/openrouter model/i)).toBeDisabled();
      expect(screen.getByLabelText(/bedrock model/i)).toBeDisabled();
      expect(screen.getByLabelText(/lmstudio model/i)).toBeDisabled();
    });

    it('should show loading state on submit button when pending', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isPending: true,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(screen.getByText('Saving...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /saving/i })).toBeDisabled();
    });

    it('should show update button text when isUpdate is true', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isUpdate: true,
        isDirty: true,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(
        screen.getByRole('button', { name: /update settings/i })
      ).toBeInTheDocument();
    });

    it('should disable submit button when form is not dirty', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isDirty: false,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(screen.getByRole('button', { name: /create settings/i })).toBeDisabled();
    });

    it('should enable submit button when form is dirty', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isDirty: true,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(screen.getByRole('button', { name: /create settings/i })).toBeEnabled();
    });
  });

  describe('Form Validation', () => {
    it('should show validation errors', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          ...defaultFormHook.form,
          formState: {
            errors: {
              provider: { message: 'Provider is required' },
              openai_model: { message: 'OpenAI model is required' },
              lmstudio_model: { message: 'LMStudio model is required' },
            },
          },
        },
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(screen.getByText('OpenAI model is required')).toBeInTheDocument();
    });

    it('should show LMStudio model validation error when provider is lmstudio', () => {
      mockProviderValue = 'lmstudio';
      const mockWatch = vi.fn().mockReturnValue('lmstudio');
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          ...defaultFormHook.form,
          watch: mockWatch,
          formState: {
            errors: {
              lmstudio_model: {
                message:
                  'LMStudio model is required when LMStudio provider is selected',
              },
            },
          },
        },
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(
        screen.getByText(
          'LMStudio model is required when LMStudio provider is selected'
        )
      ).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('should call onSubmit when form is submitted', async () => {
      const mockOnSubmit = vi.fn();
      const user = userEvent.setup();

      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        onSubmit: mockOnSubmit,
        isDirty: true,
      });

      renderWithProviders(<LlmSettingsPage />);

      const submitButton = screen.getByRole('button', { name: /create settings/i });
      await user.click(submitButton);

      expect(mockOnSubmit).toHaveBeenCalled();
    });
  });

  describe('Notifications', () => {
    it('should show success notification', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        notifications: {
          ...defaultFormHook.notifications,
          showSuccess: true,
          successMessage: 'Settings saved successfully',
        },
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(screen.getByText('Settings saved successfully')).toBeInTheDocument();
    });

    it('should show error notification', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        notifications: {
          ...defaultFormHook.notifications,
          showError: true,
          errorMessage: 'Failed to save settings',
        },
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(screen.getByText('Failed to save settings')).toBeInTheDocument();
    });

    it('should call hideSuccess when success notification is closed', async () => {
      const mockHideSuccess = vi.fn();
      const user = userEvent.setup();

      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        notifications: {
          ...defaultFormHook.notifications,
          showSuccess: true,
          successMessage: 'Settings saved successfully',
          hideSuccess: mockHideSuccess,
        },
      });

      renderWithProviders(<LlmSettingsPage />);

      const closeButton = screen.getByLabelText(/close/i);
      await user.click(closeButton);

      expect(mockHideSuccess).toHaveBeenCalled();
    });

    it('should call hideError when error notification is closed', async () => {
      const mockHideError = vi.fn();
      const user = userEvent.setup();

      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        notifications: {
          ...defaultFormHook.notifications,
          showError: true,
          errorMessage: 'Failed to save settings',
          hideError: mockHideError,
        },
      });

      renderWithProviders(<LlmSettingsPage />);

      const closeButton = screen.getByLabelText(/close/i);
      await user.click(closeButton);

      expect(mockHideError).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper form labels', () => {
      renderWithProviders(<LlmSettingsPage />);

      expect(screen.getByLabelText(/provider/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/openai model/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/openrouter model/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/bedrock model/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/lmstudio model/i)).toBeInTheDocument();
    });

    it('should have proper button roles', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        isDirty: true,
      });

      renderWithProviders(<LlmSettingsPage />);

      expect(
        screen.getByRole('button', { name: /create settings/i })
      ).toBeInTheDocument();
    });

    it('should have proper heading hierarchy', () => {
      renderWithProviders(<LlmSettingsPage />);

      expect(
        screen.getByRole('heading', { name: /llm settings/i })
      ).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing form hook data gracefully', () => {
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          register: vi.fn(),
          control: null,
          watch: vi.fn(),
          formState: { errors: {} },
        },
      });

      // Should not crash
      expect(() => renderWithProviders(<LlmSettingsPage />)).not.toThrow();
    });

    it('should handle missing models data gracefully', () => {
      mockProviderValue = 'lmstudio';
      const mockWatch = vi.fn().mockReturnValue('lmstudio');
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          ...defaultFormHook.form,
          watch: mockWatch,
        },
      });

      mockUseLMStudioModels.mockReturnValue({
        ...defaultModelsHook,
        data: null,
      });

      // Should not crash and show no models available
      expect(() => renderWithProviders(<LlmSettingsPage />)).not.toThrow();
    });

    it('should handle provider change correctly', () => {
      const mockWatch = vi.fn().mockReturnValue('openai');
      mockUseLlmSettingsForm.mockReturnValue({
        ...defaultFormHook,
        form: {
          ...defaultFormHook.form,
          watch: mockWatch,
        },
      });

      renderWithProviders(<LlmSettingsPage />);

      // Should show text field instead of dropdown when not lmstudio
      expect(
        screen.getByPlaceholderText('e.g., llama-3.2-3b-instruct')
      ).toBeInTheDocument();
    });
  });
});
