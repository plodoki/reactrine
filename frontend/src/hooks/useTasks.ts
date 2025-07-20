import {
  getTaskResult,
  listActiveTasks,
  triggerDatabaseTask,
  triggerErrorTask,
  triggerSimpleTask,
} from '@/services/tasksService';
import type {
  DatabaseTaskRequest,
  ErrorTaskRequest,
  TaskTriggerRequest,
} from '@/types/api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

// Query hooks
export const useTaskResult = (taskId: string, enabled = true) => {
  return useQuery({
    queryKey: ['task-result', taskId],
    queryFn: () => getTaskResult(taskId),
    enabled: enabled && !!taskId,
    retry: 1,
    refetchInterval: 2000, // Refetch every 2 seconds - will be handled by React Query's stale time
    staleTime: 1000, // Consider data stale after 1 second for active polling
  });
};

export const useActiveTasks = () => {
  return useQuery({
    queryKey: ['active-tasks'],
    queryFn: listActiveTasks,
    retry: 1,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Mutation hooks
export const useTriggerSimpleTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: TaskTriggerRequest) => triggerSimpleTask(request),
    onSuccess: data => {
      // Invalidate active tasks to show the new task
      queryClient.invalidateQueries({ queryKey: ['active-tasks'] });

      // Pre-populate the task result cache
      queryClient.setQueryData(['task-result', data.task_id], data);
    },
  });
};

export const useTriggerDatabaseTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: DatabaseTaskRequest) => triggerDatabaseTask(request),
    onSuccess: data => {
      // Invalidate active tasks to show the new task
      queryClient.invalidateQueries({ queryKey: ['active-tasks'] });

      // Pre-populate the task result cache
      queryClient.setQueryData(['task-result', data.task_id], data);
    },
  });
};

export const useTriggerErrorTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ErrorTaskRequest) => triggerErrorTask(request),
    onSuccess: data => {
      // Invalidate active tasks to show the new task
      queryClient.invalidateQueries({ queryKey: ['active-tasks'] });

      // Pre-populate the task result cache
      queryClient.setQueryData(['task-result', data.task_id], data);
    },
  });
};
