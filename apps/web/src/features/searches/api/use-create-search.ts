import { useAuth } from '@clerk/nextjs';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import { createSearch } from '@/features/searches/api/create-search';

export function useCreateSearch() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (query: string) => createSearch(await getToken(), query),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['searches', 'recent'] });
      void queryClient.invalidateQueries({ queryKey: ['dashboard', 'stats'] });
    },
  });
}
