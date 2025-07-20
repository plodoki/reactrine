import {
  mockActiveTasksResponse,
  mockDatabaseTaskRequest,
  mockErrorTaskRequest,
  mockGeneratedTaskResponse,
  mockGeneratedTaskResultResponse,
  mockTaskTriggerRequest,
} from '@/test/factories';
import { createMockError } from '@/test/utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  getTaskResult,
  listActiveTasks,
  triggerDatabaseTask,
  triggerErrorTask,
  triggerSimpleTask,
} from '../tasksService';

// Mock the generated API client using vi.hoisted to ensure it runs before imports
const mockTasksService = vi.hoisted(() => ({
  triggerSimpleTaskApiV1TasksSimplePost: vi.fn(),
  triggerDatabaseTaskApiV1TasksDatabasePost: vi.fn(),
  triggerErrorTaskApiV1TasksErrorPost: vi.fn(),
  getTaskResultApiV1TasksTaskIdGet: vi.fn(),
  listActiveTasksApiV1TasksGet: vi.fn(),
}));

// Mock the generated client module
vi.mock('@/lib/api-client', () => ({
  TasksService: mockTasksService,
}));

describe('TasksService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('triggerSimpleTask', () => {
    it('should trigger simple task successfully', async () => {
      // Arrange
      const request = mockTaskTriggerRequest({ message: 'Test simple task' });
      const generatedResponse = mockGeneratedTaskResponse({
        task_id: 'simple-task-123',
        status: 'PENDING',
        message: 'Simple task created successfully',
      });

      mockTasksService.triggerSimpleTaskApiV1TasksSimplePost.mockResolvedValue(
        generatedResponse
      );

      // Act
      const result = await triggerSimpleTask(request);

      // Assert
      expect(
        mockTasksService.triggerSimpleTaskApiV1TasksSimplePost
      ).toHaveBeenCalledWith({
        requestBody: {
          message: 'Test simple task',
        },
      });
      expect(result).toEqual({
        task_id: 'simple-task-123',
        status: 'PENDING',
        message: 'Simple task created successfully',
      });
    });

    it('should handle task trigger failures', async () => {
      // Arrange
      const request = mockTaskTriggerRequest();
      const error = createMockError(500, 'Internal server error');

      mockTasksService.triggerSimpleTaskApiV1TasksSimplePost.mockRejectedValue(error);

      // Act & Assert
      await expect(triggerSimpleTask(request)).rejects.toThrow('Internal server error');
      expect(
        mockTasksService.triggerSimpleTaskApiV1TasksSimplePost
      ).toHaveBeenCalledWith({
        requestBody: {
          message: 'Test task message',
        },
      });
    });

    it('should transform request correctly', async () => {
      // Arrange
      const request = mockTaskTriggerRequest({ message: 'Custom message' });
      const generatedResponse = mockGeneratedTaskResponse();

      mockTasksService.triggerSimpleTaskApiV1TasksSimplePost.mockResolvedValue(
        generatedResponse
      );

      // Act
      await triggerSimpleTask(request);

      // Assert
      expect(
        mockTasksService.triggerSimpleTaskApiV1TasksSimplePost
      ).toHaveBeenCalledWith({
        requestBody: {
          message: 'Custom message',
        },
      });
    });

    it('should handle validation errors (422)', async () => {
      // Arrange
      const request = mockTaskTriggerRequest({ message: '' });
      const error = createMockError(422, 'Validation error');

      mockTasksService.triggerSimpleTaskApiV1TasksSimplePost.mockRejectedValue(error);

      // Act & Assert
      await expect(triggerSimpleTask(request)).rejects.toThrow('Validation error');
    });
  });

  describe('triggerDatabaseTask', () => {
    it('should trigger database task successfully', async () => {
      // Arrange
      const request = mockDatabaseTaskRequest({ query: 'SELECT * FROM users LIMIT 5' });
      const generatedResponse = mockGeneratedTaskResponse({
        task_id: 'db-task-456',
        status: 'PENDING',
        message: 'Database task created successfully',
      });

      mockTasksService.triggerDatabaseTaskApiV1TasksDatabasePost.mockResolvedValue(
        generatedResponse
      );

      // Act
      const result = await triggerDatabaseTask(request);

      // Assert
      expect(
        mockTasksService.triggerDatabaseTaskApiV1TasksDatabasePost
      ).toHaveBeenCalledWith({
        requestBody: {
          query: 'SELECT * FROM users LIMIT 5',
        },
      });
      expect(result).toEqual({
        task_id: 'db-task-456',
        status: 'PENDING',
        message: 'Database task created successfully',
      });
    });

    it('should handle invalid database queries', async () => {
      // Arrange
      const request = mockDatabaseTaskRequest({ query: 'INVALID SQL QUERY' });
      const error = createMockError(422, 'Invalid SQL query');

      mockTasksService.triggerDatabaseTaskApiV1TasksDatabasePost.mockRejectedValue(
        error
      );

      // Act & Assert
      await expect(triggerDatabaseTask(request)).rejects.toThrow('Invalid SQL query');
      expect(
        mockTasksService.triggerDatabaseTaskApiV1TasksDatabasePost
      ).toHaveBeenCalledWith({
        requestBody: {
          query: 'INVALID SQL QUERY',
        },
      });
    });

    it('should handle unauthorized access (401)', async () => {
      // Arrange
      const request = mockDatabaseTaskRequest();
      const error = createMockError(401, 'Unauthorized');

      mockTasksService.triggerDatabaseTaskApiV1TasksDatabasePost.mockRejectedValue(
        error
      );

      // Act & Assert
      await expect(triggerDatabaseTask(request)).rejects.toThrow('Unauthorized');
    });

    it('should validate allowed query types', async () => {
      // Arrange
      const request = mockDatabaseTaskRequest({ query: 'DROP TABLE users' });
      const error = createMockError(422, 'Query type not allowed');

      mockTasksService.triggerDatabaseTaskApiV1TasksDatabasePost.mockRejectedValue(
        error
      );

      // Act & Assert
      await expect(triggerDatabaseTask(request)).rejects.toThrow(
        'Query type not allowed'
      );
    });
  });

  describe('triggerErrorTask', () => {
    it('should trigger error task with should_fail=false', async () => {
      // Arrange
      const request = mockErrorTaskRequest({ should_fail: false });
      const generatedResponse = mockGeneratedTaskResponse({
        task_id: 'error-task-789',
        status: 'PENDING',
        message: 'Error task created successfully',
      });

      mockTasksService.triggerErrorTaskApiV1TasksErrorPost.mockResolvedValue(
        generatedResponse
      );

      // Act
      const result = await triggerErrorTask(request);

      // Assert
      expect(mockTasksService.triggerErrorTaskApiV1TasksErrorPost).toHaveBeenCalledWith(
        {
          requestBody: {
            should_fail: false,
          },
        }
      );
      expect(result).toEqual({
        task_id: 'error-task-789',
        status: 'PENDING',
        message: 'Error task created successfully',
      });
    });

    it('should trigger error task with should_fail=true', async () => {
      // Arrange
      const request = mockErrorTaskRequest({ should_fail: true });
      const generatedResponse = mockGeneratedTaskResponse({
        task_id: 'error-task-fail-123',
        status: 'PENDING',
        message: 'Error task (will fail) created successfully',
      });

      mockTasksService.triggerErrorTaskApiV1TasksErrorPost.mockResolvedValue(
        generatedResponse
      );

      // Act
      const result = await triggerErrorTask(request);

      // Assert
      expect(mockTasksService.triggerErrorTaskApiV1TasksErrorPost).toHaveBeenCalledWith(
        {
          requestBody: {
            should_fail: true,
          },
        }
      );
      expect(result).toEqual({
        task_id: 'error-task-fail-123',
        status: 'PENDING',
        message: 'Error task (will fail) created successfully',
      });
    });

    it('should handle default should_fail value', async () => {
      // Arrange
      const request = mockErrorTaskRequest(); // should_fail defaults to false
      const generatedResponse = mockGeneratedTaskResponse();

      mockTasksService.triggerErrorTaskApiV1TasksErrorPost.mockResolvedValue(
        generatedResponse
      );

      // Act
      await triggerErrorTask(request);

      // Assert
      expect(mockTasksService.triggerErrorTaskApiV1TasksErrorPost).toHaveBeenCalledWith(
        {
          requestBody: {
            should_fail: false,
          },
        }
      );
    });

    it('should handle error task trigger failures', async () => {
      // Arrange
      const request = mockErrorTaskRequest();
      const error = createMockError(500, 'Task system error');

      mockTasksService.triggerErrorTaskApiV1TasksErrorPost.mockRejectedValue(error);

      // Act & Assert
      await expect(triggerErrorTask(request)).rejects.toThrow('Task system error');
    });
  });

  describe('getTaskResult', () => {
    it('should get task result for completed task', async () => {
      // Arrange
      const taskId = 'completed-task-123';
      const generatedResponse = mockGeneratedTaskResultResponse({
        task_id: taskId,
        status: 'SUCCESS',
        result: { data: 'Task completed successfully', count: 42 },
        error: null,
        created_at: '2024-01-01T10:00:00Z',
        completed_at: '2024-01-01T10:05:00Z',
      });

      mockTasksService.getTaskResultApiV1TasksTaskIdGet.mockResolvedValue(
        generatedResponse
      );

      // Act
      const result = await getTaskResult(taskId);

      // Assert
      expect(mockTasksService.getTaskResultApiV1TasksTaskIdGet).toHaveBeenCalledWith({
        taskId,
      });
      expect(result).toEqual({
        task_id: taskId,
        status: 'SUCCESS',
        result: { data: 'Task completed successfully', count: 42 },
        error: null,
        created_at: '2024-01-01T10:00:00Z',
        completed_at: '2024-01-01T10:05:00Z',
      });
    });

    it('should get task result for pending task', async () => {
      // Arrange
      const taskId = 'pending-task-456';
      const generatedResponse = mockGeneratedTaskResultResponse({
        task_id: taskId,
        status: 'PENDING',
        result: null,
        error: null,
        created_at: '2024-01-01T10:00:00Z',
        completed_at: null,
      });

      mockTasksService.getTaskResultApiV1TasksTaskIdGet.mockResolvedValue(
        generatedResponse
      );

      // Act
      const result = await getTaskResult(taskId);

      // Assert
      expect(result).toEqual({
        task_id: taskId,
        status: 'PENDING',
        result: null,
        error: null,
        created_at: '2024-01-01T10:00:00Z',
        completed_at: null,
      });
    });

    it('should get task result for failed task', async () => {
      // Arrange
      const taskId = 'failed-task-789';
      const generatedResponse = mockGeneratedTaskResultResponse({
        task_id: taskId,
        status: 'FAILURE',
        result: null,
        error: 'Task execution failed: Connection timeout',
        created_at: '2024-01-01T10:00:00Z',
        completed_at: '2024-01-01T10:02:00Z',
      });

      mockTasksService.getTaskResultApiV1TasksTaskIdGet.mockResolvedValue(
        generatedResponse
      );

      // Act
      const result = await getTaskResult(taskId);

      // Assert
      expect(result).toEqual({
        task_id: taskId,
        status: 'FAILURE',
        result: null,
        error: 'Task execution failed: Connection timeout',
        created_at: '2024-01-01T10:00:00Z',
        completed_at: '2024-01-01T10:02:00Z',
      });
    });

    it('should handle non-existent task IDs (404)', async () => {
      // Arrange
      const taskId = 'non-existent-task';
      const error = createMockError(404, 'Task not found');

      mockTasksService.getTaskResultApiV1TasksTaskIdGet.mockRejectedValue(error);

      // Act & Assert
      await expect(getTaskResult(taskId)).rejects.toThrow('Task not found');
      expect(mockTasksService.getTaskResultApiV1TasksTaskIdGet).toHaveBeenCalledWith({
        taskId,
      });
    });

    it('should handle undefined/null result and error fields', async () => {
      // Arrange
      const taskId = 'task-with-undefined-fields';
      const generatedResponse = mockGeneratedTaskResultResponse({
        task_id: taskId,
        status: 'SUCCESS',
        result: undefined,
        error: undefined,
        created_at: undefined,
        completed_at: undefined,
      });

      mockTasksService.getTaskResultApiV1TasksTaskIdGet.mockResolvedValue(
        generatedResponse
      );

      // Act
      const result = await getTaskResult(taskId);

      // Assert
      expect(result).toEqual({
        task_id: taskId,
        status: 'SUCCESS',
        result: null,
        error: null,
        created_at: null,
        completed_at: null,
      });
    });
  });

  describe('listActiveTasks', () => {
    it('should list active tasks', async () => {
      // Arrange
      const activeTasksResponse = mockActiveTasksResponse({
        'active-task-1': {
          name: 'simple_task',
          state: 'PENDING',
          received: 1704096000.0,
          args: ['Test message'],
        },
        'active-task-2': {
          name: 'database_task',
          state: 'STARTED',
          received: 1704096300.0,
          args: ['SELECT * FROM users'],
        },
      });

      mockTasksService.listActiveTasksApiV1TasksGet.mockResolvedValue(
        activeTasksResponse
      );

      // Act
      const result = await listActiveTasks();

      // Assert
      expect(mockTasksService.listActiveTasksApiV1TasksGet).toHaveBeenCalledWith();
      expect(result).toEqual(activeTasksResponse);
    });

    it('should handle empty active tasks list', async () => {
      // Arrange
      const emptyResponse = {};

      mockTasksService.listActiveTasksApiV1TasksGet.mockResolvedValue(emptyResponse);

      // Act
      const result = await listActiveTasks();

      // Assert
      expect(result).toEqual({});
    });

    it('should handle Flower service unavailable (503)', async () => {
      // Arrange
      const error = createMockError(503, 'Flower service unavailable');

      mockTasksService.listActiveTasksApiV1TasksGet.mockRejectedValue(error);

      // Act & Assert
      await expect(listActiveTasks()).rejects.toThrow('Flower service unavailable');
    });

    it('should handle unauthorized access (401)', async () => {
      // Arrange
      const error = createMockError(401, 'Unauthorized');

      mockTasksService.listActiveTasksApiV1TasksGet.mockRejectedValue(error);

      // Act & Assert
      await expect(listActiveTasks()).rejects.toThrow('Unauthorized');
    });

    it('should handle complex active tasks data', async () => {
      // Arrange
      const complexResponse = {
        'task-1': {
          name: 'complex_task',
          state: 'SUCCESS',
          received: 1704096000.0,
          started: 1704096001.0,
          succeeded: 1704096005.0,
          args: ['arg1', 'arg2'],
          kwargs: { key: 'value' },
          result: { success: true },
        },
        'task-2': {
          name: 'failed_task',
          state: 'FAILURE',
          received: 1704096100.0,
          started: 1704096101.0,
          failed: 1704096102.0,
          exception: 'ValueError: Invalid input',
          traceback: 'Traceback (most recent call last)...',
        },
      };

      mockTasksService.listActiveTasksApiV1TasksGet.mockResolvedValue(complexResponse);

      // Act
      const result = await listActiveTasks();

      // Assert
      expect(result).toEqual(complexResponse);
    });
  });
});
