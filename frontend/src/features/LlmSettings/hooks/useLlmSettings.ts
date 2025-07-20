import { CreateLLMSettings, LLMSettings } from '@/types/api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createSettings,
  fetchLMStudioModels,
  fetchSettings,
  updateSettings,
} from '../services/llmSettingsService';

export const useLlmSettings = () => {
  return useQuery({
    queryKey: ['llm-settings'],
    queryFn: fetchSettings,
    retry: 1, // Only retry once for failed requests
  });
};

export const useUpdateLlmSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: Partial<LLMSettings>) => updateSettings(payload),
    onSuccess: newData => {
      // Update the cache with the new data
      queryClient.setQueryData(['llm-settings'], newData);
    },
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    onError: _error => {
      // Invalidate queries to refetch the current state
      queryClient.invalidateQueries({ queryKey: ['llm-settings'] });
    },
  });
};

export const useCreateLlmSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateLLMSettings) => createSettings(payload),
    onSuccess: newData => {
      // Update the cache with the new data
      queryClient.setQueryData(['llm-settings'], newData);
    },
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    onError: _error => {
      // Invalidate queries to refetch the current state
      queryClient.invalidateQueries({ queryKey: ['llm-settings'] });
    },
  });
};

export const useLMStudioModels = () => {
  return useQuery({
    queryKey: ['lmstudio-models'],
    queryFn: fetchLMStudioModels,
    retry: 1, // Only retry once for failed requests
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: false, // Only fetch when explicitly triggered
  });
};
