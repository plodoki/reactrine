import { useNotifications } from '@/hooks/useNotifications';
import {
  ApiKeysService,
  type ApiKeyCreate,
  type ApiKeyCreated,
  type ApiKeyInfo,
  type ApiKeyList,
} from '@/lib/api-client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

export const useApiKeys = () => {
  return useQuery({
    queryKey: ['api-keys'],
    queryFn: async (): Promise<ApiKeyInfo[]> => {
      const response: ApiKeyList =
        await ApiKeysService.listApiKeysApiV1UsersMeApiKeysGet();
      return response.keys;
    },
    retry: 1, // Only retry once for failed requests
  });
};

export const useCreateApiKey = () => {
  const queryClient = useQueryClient();
  const notifications = useNotifications();

  return useMutation({
    mutationFn: async (request: ApiKeyCreate) =>
      await ApiKeysService.createApiKeyApiV1UsersMeApiKeysPost({
        requestBody: request,
      }),
    onSuccess: (response: ApiKeyCreated) => {
      // Update the cache with the new key
      queryClient.setQueryData(['api-keys'], (oldData: ApiKeyInfo[] | undefined) => {
        if (!oldData) return [response.api_key];
        return [response.api_key, ...oldData];
      });
      notifications.showSuccessNotification('API key created successfully!');
    },
    onError: error => {
      notifications.showErrorNotification(error, 'Failed to create API key');
      // Invalidate queries to refetch the current state
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
};

export const useRevokeApiKey = () => {
  const queryClient = useQueryClient();
  const notifications = useNotifications();

  return useMutation({
    mutationFn: async (keyId: number) =>
      await ApiKeysService.revokeApiKeyApiV1UsersMeApiKeysKeyIdDelete({ keyId }),
    onSuccess: (_data, keyId) => {
      // Update the cache to mark the key as revoked
      queryClient.setQueryData(['api-keys'], (oldData: ApiKeyInfo[] | undefined) => {
        if (!oldData) return oldData;
        return oldData.map(key =>
          key.id === keyId ? { ...key, is_active: false } : key
        );
      });
      notifications.showSuccessNotification('API key revoked successfully!');
    },
    onError: error => {
      notifications.showErrorNotification(error, 'Failed to revoke API key');
      // Invalidate queries to refetch the current state
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });
};
