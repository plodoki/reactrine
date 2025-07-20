import { act, renderHook } from '@testing-library/react';
import { ApiError } from '@/types/api';
import { useNotifications } from '../useNotifications';

describe('useNotifications', () => {
  it('should initialize with default state', () => {
    const { result } = renderHook(() => useNotifications());

    expect(result.current.showSuccess).toBe(false);
    expect(result.current.showError).toBe(false);
    expect(result.current.errorMessage).toBe('');
    expect(result.current.successMessage).toBe('');
  });

  it('should show success notification', () => {
    const { result } = renderHook(() => useNotifications());

    act(() => {
      result.current.showSuccessNotification('Success message');
    });

    expect(result.current.showSuccess).toBe(true);
    expect(result.current.successMessage).toBe('Success message');
  });

  it('should show error notification with custom message', () => {
    const { result } = renderHook(() => useNotifications());
    const error = new Error('Test error');

    act(() => {
      result.current.showErrorNotification(error);
    });

    expect(result.current.showError).toBe(true);
    expect(result.current.errorMessage).toBe('Test error');
  });

  it('should handle API error with status codes', () => {
    const { result } = renderHook(() => useNotifications());
    const apiError = new ApiError('Request failed', {
      status: 401,
      statusText: 'Unauthorized',
      data: {},
    });

    act(() => {
      result.current.showErrorNotification(apiError);
    });

    expect(result.current.showError).toBe(true);
    expect(result.current.errorMessage).toBe('Authentication required. Please log in.');
  });

  it('should handle API error with 403 status', () => {
    const { result } = renderHook(() => useNotifications());
    const apiError = new ApiError('Forbidden', {
      status: 403,
      statusText: 'Forbidden',
      data: {},
    });

    act(() => {
      result.current.showErrorNotification(apiError);
    });

    expect(result.current.showError).toBe(true);
    expect(result.current.errorMessage).toBe(
      'Access denied. You do not have permission to perform this action.'
    );
  });

  it('should handle API error with validation details', () => {
    const { result } = renderHook(() => useNotifications());
    const apiError = new ApiError('Validation failed', {
      status: 422,
      statusText: 'Unprocessable Entity',
      data: {
        detail: [{ msg: 'Field is required' }, { message: 'Invalid format' }],
      },
    });

    act(() => {
      result.current.showErrorNotification(apiError);
    });

    expect(result.current.showError).toBe(true);
    expect(result.current.errorMessage).toBe('Field is required, Invalid format');
  });

  it('should show success notification with default message', () => {
    const { result } = renderHook(() => useNotifications());

    act(() => {
      result.current.showSuccessNotification();
    });

    expect(result.current.showSuccess).toBe(true);
    expect(result.current.successMessage).toBe('Operation completed successfully!');
  });

  it('should hide success notification', () => {
    const { result } = renderHook(() => useNotifications());

    act(() => {
      result.current.showSuccessNotification('Success');
    });

    expect(result.current.showSuccess).toBe(true);

    act(() => {
      result.current.hideSuccess();
    });

    expect(result.current.showSuccess).toBe(false);
  });

  it('should hide error notification', () => {
    const { result } = renderHook(() => useNotifications());

    act(() => {
      result.current.showErrorNotification(new Error('Test error'));
    });

    expect(result.current.showError).toBe(true);

    act(() => {
      result.current.hideError();
    });

    expect(result.current.showError).toBe(false);
  });

  it('should clear all notifications', () => {
    const { result } = renderHook(() => useNotifications());

    act(() => {
      result.current.showSuccessNotification('Success');
      result.current.showErrorNotification(new Error('Error'));
    });

    expect(result.current.showSuccess).toBe(true);
    expect(result.current.showError).toBe(true);

    act(() => {
      result.current.clearAll();
    });

    expect(result.current.showSuccess).toBe(false);
    expect(result.current.showError).toBe(false);
    expect(result.current.successMessage).toBe('');
    expect(result.current.errorMessage).toBe('');
  });
});
