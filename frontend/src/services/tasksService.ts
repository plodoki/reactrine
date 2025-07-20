import type {
  DatabaseTaskRequest as GeneratedDatabaseTaskRequest,
  ErrorTaskRequest as GeneratedErrorTaskRequest,
  TaskResponse as GeneratedTaskResponse,
  TaskResultResponse as GeneratedTaskResultResponse,
  TaskTriggerRequest as GeneratedTaskTriggerRequest,
} from '@/lib/api-client';
import { TasksService } from '@/lib/api-client';
import type {
  ActiveTasksResponse,
  DatabaseTaskRequest,
  ErrorTaskRequest,
  TaskResponse,
  TaskResultResponse,
  TaskTriggerRequest,
} from '@/types/api';

// Simple Task Operations
export const triggerSimpleTask = async (
  request: TaskTriggerRequest
): Promise<TaskResponse> => {
  const requestBody: GeneratedTaskTriggerRequest = {
    message: request.message,
  };

  const response: GeneratedTaskResponse =
    await TasksService.triggerSimpleTaskApiV1TasksSimplePost({
      requestBody,
    });

  return {
    task_id: response.task_id,
    status: response.status,
    message: response.message,
  };
};

// Database Task Operations
export const triggerDatabaseTask = async (
  request: DatabaseTaskRequest
): Promise<TaskResponse> => {
  const requestBody: GeneratedDatabaseTaskRequest = {
    query: request.query,
  };

  const response: GeneratedTaskResponse =
    await TasksService.triggerDatabaseTaskApiV1TasksDatabasePost({
      requestBody,
    });

  return {
    task_id: response.task_id,
    status: response.status,
    message: response.message,
  };
};

// Error Task Operations
export const triggerErrorTask = async (
  request: ErrorTaskRequest
): Promise<TaskResponse> => {
  const requestBody: GeneratedErrorTaskRequest = {
    should_fail: request.should_fail,
  };

  const response: GeneratedTaskResponse =
    await TasksService.triggerErrorTaskApiV1TasksErrorPost({
      requestBody,
    });

  return {
    task_id: response.task_id,
    status: response.status,
    message: response.message,
  };
};

// Task Status and Results
export const getTaskResult = async (taskId: string): Promise<TaskResultResponse> => {
  const response: GeneratedTaskResultResponse =
    await TasksService.getTaskResultApiV1TasksTaskIdGet({
      taskId,
    });

  return {
    task_id: response.task_id,
    status: response.status,
    result: response.result || null,
    error: response.error || null,
    created_at: response.created_at || null,
    completed_at: response.completed_at || null,
  };
};

// Active Tasks Management
export const listActiveTasks = async (): Promise<ActiveTasksResponse> => {
  const response: Record<string, unknown> =
    await TasksService.listActiveTasksApiV1TasksGet();
  return response;
};
