import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import { JSX, ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// Import types
import type { TaskResponse } from '@/types/api';

import {
  mockActiveTasksResponse,
  mockDatabaseTaskRequest,
  mockErrorTaskRequest,
  mockTaskResponse,
  mockTaskResultResponse,
  mockTaskTriggerRequest,
} from '@/test/factories';
import { createMockError } from '@/test/utils';

// Mock the tasks service
vi.mock('@/services/tasksService', () => ({
  getTaskResult: vi.fn(),
  listActiveTasks: vi.fn(),
  triggerSimpleTask: vi.fn(),
  triggerDatabaseTask: vi.fn(),
  triggerErrorTask: vi.fn(),
}));

import {
  getTaskResult,
  listActiveTasks,
  triggerDatabaseTask,
  triggerErrorTask,
  triggerSimpleTask,
} from '@/services/tasksService';

import {
  useActiveTasks,
  useTaskResult,
  useTriggerDatabaseTask,
  useTriggerErrorTask,
  useTriggerSimpleTask,
} from '../useTasks';

describe('useTasks Hooks', () => {
  let queryClient: QueryClient;
  let wrapper: ({ children }: { children: ReactNode }) => JSX.Element;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: 1, // Allow 1 retry for error testing
          gcTime: 0,
          staleTime: 0,
        },
        mutations: {
          retry: false,
          gcTime: 0,
        },
      },
    });

    wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    vi.clearAllMocks();
  });

  describe('useTaskResult', () => {
    it('should fetch task result successfully', async () => {
      // Arrange
      const taskId = 'task-123';
      const mockResult = mockTaskResultResponse({
        task_id: taskId,
        status: 'SUCCESS',
        result: { message: 'Task completed successfully' },
        created_at: '2024-01-01T00:00:00Z',
        completed_at: '2024-01-01T00:01:00Z',
      });
      vi.mocked(getTaskResult).mockResolvedValue(mockResult);

      // Act
      const { result } = renderHook(() => useTaskResult(taskId), { wrapper });

      // Assert
      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResult);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(getTaskResult).toHaveBeenCalledWith(taskId);
      expect(getTaskResult).toHaveBeenCalledTimes(1);
    });

    it('should handle pending task status', async () => {
      // Arrange
      const taskId = 'task-456';
      const mockResult = mockTaskResultResponse({
        task_id: taskId,
        status: 'PENDING',
        result: null,
        error: null,
        created_at: '2024-01-01T00:00:00Z',
        completed_at: null,
      });
      vi.mocked(getTaskResult).mockResolvedValue(mockResult);

      // Act
      const { result } = renderHook(() => useTaskResult(taskId), { wrapper });

      // Assert
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResult);
      expect(result.current.data?.status).toBe('PENDING');
      expect(result.current.data?.result).toBeNull();
      expect(result.current.data?.completed_at).toBeNull();
    });

    it('should handle failed task status', async () => {
      // Arrange
      const taskId = 'task-789';
      const mockResult = mockTaskResultResponse({
        task_id: taskId,
        status: 'FAILURE',
        result: null,
        error: 'Task execution failed',
        created_at: '2024-01-01T00:00:00Z',
        completed_at: '2024-01-01T00:01:00Z',
      });
      vi.mocked(getTaskResult).mockResolvedValue(mockResult);

      // Act
      const { result } = renderHook(() => useTaskResult(taskId), { wrapper });

      // Assert
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResult);
      expect(result.current.data?.status).toBe('FAILURE');
      expect(result.current.data?.error).toBe('Task execution failed');
      expect(result.current.data?.result).toBeNull();
    });

    it('should handle task not found errors (404)', async () => {
      // Arrange
      const taskId = 'nonexistent-task';
      const error = createMockError(404, 'Task not found');
      vi.mocked(getTaskResult).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTaskResult(taskId), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const taskId = 'task-unauthorized';
      const error = createMockError(401, 'Unauthorized');
      vi.mocked(getTaskResult).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTaskResult(taskId), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle server errors (500)', async () => {
      // Arrange
      const taskId = 'task-server-error';
      const error = createMockError(500, 'Internal Server Error');
      vi.mocked(getTaskResult).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTaskResult(taskId), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should respect enabled parameter', async () => {
      // Arrange
      const taskId = 'task-disabled';
      const mockResult = mockTaskResultResponse({ task_id: taskId });
      vi.mocked(getTaskResult).mockResolvedValue(mockResult);

      // Act
      const { result } = renderHook(() => useTaskResult(taskId, false), { wrapper });

      // Assert - should not make any requests when disabled
      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBeNull();
      expect(getTaskResult).not.toHaveBeenCalled();
    });

    it('should not fetch when taskId is empty', async () => {
      // Arrange
      const mockResult = mockTaskResultResponse({ task_id: '' });
      vi.mocked(getTaskResult).mockResolvedValue(mockResult);

      // Act
      const { result } = renderHook(() => useTaskResult(''), { wrapper });

      // Assert - should not make any requests when taskId is empty
      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBeNull();
      expect(getTaskResult).not.toHaveBeenCalled();
    });

    it('should retry only once on failure', async () => {
      // Arrange
      const taskId = 'task-retry';
      const error = createMockError(500, 'Server Error');
      vi.mocked(getTaskResult).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTaskResult(taskId), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      // Should have been called twice (initial + 1 retry)
      expect(getTaskResult).toHaveBeenCalledTimes(2);
    });

    it('should handle complex task result data', async () => {
      // Arrange
      const taskId = 'task-complex';
      const mockResult = mockTaskResultResponse({
        task_id: taskId,
        status: 'SUCCESS',
        result: {
          data: { count: 42, items: ['item1', 'item2'] },
          metadata: { processed_at: '2024-01-01T00:01:00Z' },
        },
        created_at: '2024-01-01T00:00:00Z',
        completed_at: '2024-01-01T00:01:00Z',
      });
      vi.mocked(getTaskResult).mockResolvedValue(mockResult);

      // Act
      const { result } = renderHook(() => useTaskResult(taskId), { wrapper });

      // Assert
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResult);
      expect(result.current.data?.result).toEqual({
        data: { count: 42, items: ['item1', 'item2'] },
        metadata: { processed_at: '2024-01-01T00:01:00Z' },
      });
    });
  });

  describe('useActiveTasks', () => {
    it('should list active tasks successfully', async () => {
      // Arrange
      const mockTasks = mockActiveTasksResponse({
        'task-1': { status: 'PENDING', name: 'Simple Task' },
        'task-2': { status: 'STARTED', name: 'Database Task' },
      });
      vi.mocked(listActiveTasks).mockResolvedValue(mockTasks);

      // Act
      const { result } = renderHook(() => useActiveTasks(), { wrapper });

      // Assert
      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockTasks);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(listActiveTasks).toHaveBeenCalledTimes(1);
    });

    it('should handle empty active tasks list', async () => {
      // Arrange
      vi.mocked(listActiveTasks).mockResolvedValue({});

      // Act
      const { result } = renderHook(() => useActiveTasks(), { wrapper });

      // Assert
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual({});
      expect(result.current.isLoading).toBe(false);
    });

    it('should handle Flower service unavailable (503)', async () => {
      // Arrange
      const error = createMockError(503, 'Service Unavailable');
      vi.mocked(listActiveTasks).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useActiveTasks(), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const error = createMockError(401, 'Unauthorized');
      vi.mocked(listActiveTasks).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useActiveTasks(), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle server errors (500)', async () => {
      // Arrange
      const error = createMockError(500, 'Internal Server Error');
      vi.mocked(listActiveTasks).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useActiveTasks(), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should retry only once on failure', async () => {
      // Arrange
      const error = createMockError(500, 'Server Error');
      vi.mocked(listActiveTasks).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useActiveTasks(), { wrapper });

      // Assert
      await waitFor(
        () => {
          expect(result.current.isError).toBe(true);
        },
        { timeout: 5000 }
      );

      // Should have been called twice (initial + 1 retry)
      expect(listActiveTasks).toHaveBeenCalledTimes(2);
    });

    it('should handle complex active tasks data', async () => {
      // Arrange
      const mockTasks = {
        'task-complex-1': {
          status: 'STARTED',
          name: 'Complex Task',
          worker: 'worker-1',
          timestamp: 1704067200,
          args: ['arg1', 'arg2'],
          kwargs: { key: 'value' },
        },
        'task-complex-2': {
          status: 'PENDING',
          name: 'Another Task',
          worker: 'worker-2',
          timestamp: 1704067260,
          args: [],
          kwargs: {},
        },
      };
      vi.mocked(listActiveTasks).mockResolvedValue(mockTasks);

      // Act
      const { result } = renderHook(() => useActiveTasks(), { wrapper });

      // Assert
      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockTasks);
      expect(Object.keys(result.current.data!)).toHaveLength(2);
    });
  });

  describe('useTriggerSimpleTask', () => {
    it('should trigger simple task successfully', async () => {
      // Arrange
      const mockRequest = mockTaskTriggerRequest({ message: 'Test simple task' });
      const mockResponse = mockTaskResponse({
        task_id: 'simple-task-123',
        status: 'PENDING',
        message: 'Simple task triggered successfully',
      });
      vi.mocked(triggerSimpleTask).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useTriggerSimpleTask(), { wrapper });

      // Assert - initial state
      expect(result.current.isIdle).toBe(true);
      expect(result.current.isPending).toBe(false);
      expect(result.current.data).toBeUndefined();

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.isPending).toBe(false);
      expect(result.current.error).toBeNull();
      expect(triggerSimpleTask).toHaveBeenCalledWith(mockRequest);
      expect(triggerSimpleTask).toHaveBeenCalledTimes(1);
    });

    it('should handle task trigger failures', async () => {
      // Arrange
      const mockRequest = mockTaskTriggerRequest({ message: 'Failed task' });
      const error = createMockError(500, 'Task trigger failed');
      vi.mocked(triggerSimpleTask).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTriggerSimpleTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
      expect(result.current.isPending).toBe(false);
    });

    it('should handle validation errors (422)', async () => {
      // Arrange
      const mockRequest = mockTaskTriggerRequest({ message: '' });
      const error = createMockError(422, 'Validation Error');
      vi.mocked(triggerSimpleTask).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTriggerSimpleTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const mockRequest = mockTaskTriggerRequest({ message: 'Unauthorized task' });
      const error = createMockError(401, 'Unauthorized');
      vi.mocked(triggerSimpleTask).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTriggerSimpleTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should invalidate active tasks on success', async () => {
      // Arrange
      const mockRequest = mockTaskTriggerRequest({ message: 'Task with cache update' });
      const mockResponse = mockTaskResponse({
        task_id: 'cache-task-123',
        status: 'PENDING',
        message: 'Task triggered',
      });
      vi.mocked(triggerSimpleTask).mockResolvedValue(mockResponse);

      // Spy on queryClient invalidateQueries
      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

      // Act
      const { result } = renderHook(() => useTriggerSimpleTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Assert - mutation was successful and service was called
      expect(result.current.data).toEqual(mockResponse);
      expect(triggerSimpleTask).toHaveBeenCalledWith(mockRequest);

      // Assert - cache was invalidated
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['active-tasks'] });
    });

    it('should pre-populate task result cache on success', async () => {
      // Arrange
      const mockRequest = mockTaskTriggerRequest({ message: 'Task with result cache' });
      const mockResponse = mockTaskResponse({
        task_id: 'result-task-123',
        status: 'PENDING',
        message: 'Task triggered',
      });
      vi.mocked(triggerSimpleTask).mockResolvedValue(mockResponse);

      // Spy on queryClient setQueryData
      const setQueryDataSpy = vi.spyOn(queryClient, 'setQueryData');

      // Act
      const { result } = renderHook(() => useTriggerSimpleTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Assert - mutation was successful and returned correct data
      expect(result.current.data).toEqual(mockResponse);
      expect(triggerSimpleTask).toHaveBeenCalledWith(mockRequest);

      // Assert - task result cache was pre-populated
      expect(setQueryDataSpy).toHaveBeenCalledWith(
        ['task-result', 'result-task-123'],
        mockResponse
      );
    });

    it('should show loading state during task trigger', async () => {
      // Arrange
      const mockRequest = mockTaskTriggerRequest({ message: 'Loading task' });
      let resolvePromise: (value: TaskResponse) => void;
      const promise = new Promise<TaskResponse>(resolve => {
        resolvePromise = resolve;
      });
      vi.mocked(triggerSimpleTask).mockReturnValue(promise);

      // Act
      const { result } = renderHook(() => useTriggerSimpleTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert - should be pending after mutation is triggered
      await waitFor(() => {
        expect(result.current.isPending).toBe(true);
      });
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBeNull();

      // Resolve the promise
      const mockResponse = mockTaskResponse({
        task_id: 'loading-task-123',
        status: 'PENDING',
        message: 'Task triggered',
      });
      resolvePromise!(mockResponse);

      await waitFor(() => {
        expect(result.current.isPending).toBe(false);
      });
    });
  });

  describe('useTriggerDatabaseTask', () => {
    it('should trigger database task successfully', async () => {
      // Arrange
      const mockRequest = mockDatabaseTaskRequest({
        query: 'SELECT * FROM users LIMIT 10',
      });
      const mockResponse = mockTaskResponse({
        task_id: 'db-task-123',
        status: 'PENDING',
        message: 'Database task triggered successfully',
      });
      vi.mocked(triggerDatabaseTask).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useTriggerDatabaseTask(), { wrapper });

      // Assert - initial state
      expect(result.current.isIdle).toBe(true);
      expect(result.current.isPending).toBe(false);
      expect(result.current.data).toBeUndefined();

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.isPending).toBe(false);
      expect(result.current.error).toBeNull();
      expect(triggerDatabaseTask).toHaveBeenCalledWith(mockRequest);
      expect(triggerDatabaseTask).toHaveBeenCalledTimes(1);
    });

    it('should handle invalid database queries', async () => {
      // Arrange
      const mockRequest = mockDatabaseTaskRequest({ query: 'INVALID SQL QUERY' });
      const error = createMockError(422, 'Invalid SQL query');
      vi.mocked(triggerDatabaseTask).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTriggerDatabaseTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle unauthorized access (401)', async () => {
      // Arrange
      const mockRequest = mockDatabaseTaskRequest({
        query: 'SELECT * FROM sensitive_data',
      });
      const error = createMockError(401, 'Unauthorized');
      vi.mocked(triggerDatabaseTask).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTriggerDatabaseTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle server errors (500)', async () => {
      // Arrange
      const mockRequest = mockDatabaseTaskRequest({ query: 'SELECT * FROM users' });
      const error = createMockError(500, 'Database connection failed');
      vi.mocked(triggerDatabaseTask).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTriggerDatabaseTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should invalidate active tasks on success', async () => {
      // Arrange
      const mockRequest = mockDatabaseTaskRequest({
        query: 'SELECT COUNT(*) FROM users',
      });
      const mockResponse = mockTaskResponse({
        task_id: 'db-cache-task-123',
        status: 'PENDING',
        message: 'Database task triggered',
      });
      vi.mocked(triggerDatabaseTask).mockResolvedValue(mockResponse);

      // Spy on queryClient invalidateQueries
      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

      // Act
      const { result } = renderHook(() => useTriggerDatabaseTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Assert - mutation was successful and service was called
      expect(result.current.data).toEqual(mockResponse);
      expect(triggerDatabaseTask).toHaveBeenCalledWith(mockRequest);

      // Assert - cache was invalidated
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['active-tasks'] });
    });

    it('should pre-populate task result cache on success', async () => {
      // Arrange
      const mockRequest = mockDatabaseTaskRequest({ query: 'SELECT * FROM users' });
      const mockResponse = mockTaskResponse({
        task_id: 'db-result-task-123',
        status: 'PENDING',
        message: 'Database task triggered',
      });
      vi.mocked(triggerDatabaseTask).mockResolvedValue(mockResponse);

      // Spy on queryClient setQueryData
      const setQueryDataSpy = vi.spyOn(queryClient, 'setQueryData');

      // Act
      const { result } = renderHook(() => useTriggerDatabaseTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Assert - mutation was successful and returned correct data
      expect(result.current.data).toEqual(mockResponse);
      expect(triggerDatabaseTask).toHaveBeenCalledWith(mockRequest);

      // Assert - task result cache was pre-populated
      expect(setQueryDataSpy).toHaveBeenCalledWith(
        ['task-result', 'db-result-task-123'],
        mockResponse
      );
    });
  });

  describe('useTriggerErrorTask', () => {
    it('should trigger error task with should_fail=false', async () => {
      // Arrange
      const mockRequest = mockErrorTaskRequest({ should_fail: false });
      const mockResponse = mockTaskResponse({
        task_id: 'error-task-123',
        status: 'PENDING',
        message: 'Error task triggered successfully',
      });
      vi.mocked(triggerErrorTask).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useTriggerErrorTask(), { wrapper });

      // Assert - initial state
      expect(result.current.isIdle).toBe(true);
      expect(result.current.isPending).toBe(false);
      expect(result.current.data).toBeUndefined();

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(result.current.isPending).toBe(false);
      expect(result.current.error).toBeNull();
      expect(triggerErrorTask).toHaveBeenCalledWith(mockRequest);
      expect(triggerErrorTask).toHaveBeenCalledTimes(1);
    });

    it('should trigger error task with should_fail=true', async () => {
      // Arrange
      const mockRequest = mockErrorTaskRequest({ should_fail: true });
      const mockResponse = mockTaskResponse({
        task_id: 'error-task-456',
        status: 'PENDING',
        message: 'Error task triggered (will fail)',
      });
      vi.mocked(triggerErrorTask).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useTriggerErrorTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(triggerErrorTask).toHaveBeenCalledWith(mockRequest);
    });

    it('should handle default should_fail value', async () => {
      // Arrange
      const mockRequest = mockErrorTaskRequest({}); // No should_fail specified
      const mockResponse = mockTaskResponse({
        task_id: 'error-task-default',
        status: 'PENDING',
        message: 'Error task triggered with default',
      });
      vi.mocked(triggerErrorTask).mockResolvedValue(mockResponse);

      // Act
      const { result } = renderHook(() => useTriggerErrorTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockResponse);
      expect(triggerErrorTask).toHaveBeenCalledWith(mockRequest);
    });

    it('should handle error task trigger failures', async () => {
      // Arrange
      const mockRequest = mockErrorTaskRequest({ should_fail: false });
      const error = createMockError(500, 'Failed to trigger error task');
      vi.mocked(triggerErrorTask).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTriggerErrorTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
      expect(result.current.isPending).toBe(false);
    });

    it('should handle authentication errors (401)', async () => {
      // Arrange
      const mockRequest = mockErrorTaskRequest({ should_fail: true });
      const error = createMockError(401, 'Unauthorized');
      vi.mocked(triggerErrorTask).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTriggerErrorTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should handle validation errors (422)', async () => {
      // Arrange
      const mockRequest = mockErrorTaskRequest({ should_fail: true });
      const error = createMockError(422, 'Validation Error');
      vi.mocked(triggerErrorTask).mockRejectedValue(error);

      // Act
      const { result } = renderHook(() => useTriggerErrorTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      // Assert
      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeUndefined();
    });

    it('should invalidate active tasks on success', async () => {
      // Arrange
      const mockRequest = mockErrorTaskRequest({ should_fail: false });
      const mockResponse = mockTaskResponse({
        task_id: 'error-cache-task-123',
        status: 'PENDING',
        message: 'Error task triggered',
      });
      vi.mocked(triggerErrorTask).mockResolvedValue(mockResponse);

      // Spy on queryClient invalidateQueries
      const invalidateQueriesSpy = vi.spyOn(queryClient, 'invalidateQueries');

      // Act
      const { result } = renderHook(() => useTriggerErrorTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Assert - mutation was successful and service was called
      expect(result.current.data).toEqual(mockResponse);
      expect(triggerErrorTask).toHaveBeenCalledWith(mockRequest);

      // Assert - cache was invalidated
      expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: ['active-tasks'] });
    });

    it('should pre-populate task result cache on success', async () => {
      // Arrange
      const mockRequest = mockErrorTaskRequest({ should_fail: true });
      const mockResponse = mockTaskResponse({
        task_id: 'error-result-task-123',
        status: 'PENDING',
        message: 'Error task triggered',
      });
      vi.mocked(triggerErrorTask).mockResolvedValue(mockResponse);

      // Spy on queryClient setQueryData
      const setQueryDataSpy = vi.spyOn(queryClient, 'setQueryData');

      // Act
      const { result } = renderHook(() => useTriggerErrorTask(), { wrapper });

      // Trigger the mutation
      result.current.mutate(mockRequest);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Assert - mutation was successful and returned correct data
      expect(result.current.data).toEqual(mockResponse);
      expect(triggerErrorTask).toHaveBeenCalledWith(mockRequest);

      // Assert - task result cache was pre-populated
      expect(setQueryDataSpy).toHaveBeenCalledWith(
        ['task-result', 'error-result-task-123'],
        mockResponse
      );
    });
  });
});
