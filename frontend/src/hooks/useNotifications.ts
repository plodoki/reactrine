import { useCallback, useState } from 'react';
import { ApiError } from '@/types/api';

export interface NotificationState {
  showSuccess: boolean;
  showError: boolean;
  errorMessage: string;
  successMessage: string;
}

export interface NotificationActions {
  showSuccessNotification: (message?: string) => void;
  showErrorNotification: (error: unknown, fallbackMessage?: string) => void;
  hideSuccess: () => void;
  hideError: () => void;
  clearAll: () => void;
}

export function useNotifications(): NotificationState & NotificationActions {
  const [showSuccess, setShowSuccess] = useState(false);
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const showSuccessNotification = useCallback(
    (message = 'Operation completed successfully!') => {
      setSuccessMessage(message);
      setShowSuccess(true);
    },
    []
  );

  const showErrorNotification = useCallback(
    (error: unknown, fallbackMessage = 'An unexpected error occurred') => {
      let message = fallbackMessage;

      if (ApiError.isApiError(error)) {
        if (error.response?.status === 401) {
          message = 'Authentication required. Please log in.';
        } else if (error.response?.status === 403) {
          message = 'Access denied. You do not have permission to perform this action.';
        } else if (error.response?.status === 404) {
          message = 'Resource not found.';
        } else if (error.response?.status === 409) {
          message = 'Resource already exists.';
        } else if (error.response && error.response.status >= 500) {
          message = 'Server error occurred. Please try again later.';
        } else if (error.response?.data?.error) {
          message = error.response.data.error;
        } else if (error.response?.data?.detail) {
          // Handle Pydantic validation errors
          const detail = error.response.data.detail;
          if (Array.isArray(detail)) {
            message = detail
              .map((err: unknown) => {
                if (typeof err === 'object' && err !== null) {
                  const errorObj = err as Record<string, unknown>;
                  return errorObj.msg || errorObj.message || String(err);
                }
                return String(err);
              })
              .join(', ');
          } else if (typeof detail === 'string') {
            message = detail;
          } else {
            message = error.message || 'Network error occurred';
          }
        } else {
          message = error.message || 'Network error occurred';
        }
      } else if (error instanceof Error) {
        message = error.message;
      }

      setErrorMessage(message);
      setShowError(true);
    },
    []
  );

  const hideSuccess = useCallback(() => {
    setShowSuccess(false);
  }, []);

  const hideError = useCallback(() => {
    setShowError(false);
  }, []);

  const clearAll = useCallback(() => {
    setShowSuccess(false);
    setShowError(false);
    setErrorMessage('');
    setSuccessMessage('');
  }, []);

  return {
    showSuccess,
    showError,
    errorMessage,
    successMessage,
    showSuccessNotification,
    showErrorNotification,
    hideSuccess,
    hideError,
    clearAll,
  };
}
