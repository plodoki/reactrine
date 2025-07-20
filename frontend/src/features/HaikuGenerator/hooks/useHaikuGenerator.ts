import { useMutation } from '@tanstack/react-query';
import { generateHaiku } from '@/features/HaikuGenerator/services/haikuService';
import { HaikuRequest } from '@/types/api';

export const useHaikuGenerator = () => {
  return useMutation({
    mutationFn: (request: HaikuRequest) => generateHaiku(request),
  });
};
