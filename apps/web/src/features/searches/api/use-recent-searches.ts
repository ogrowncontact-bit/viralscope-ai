import { useAuth } from '@clerk/nextjs';
import { useQuery } from '@tanstack/react-query';

import { getRecentSearches } from '@/features/searches/api/get-recent-searches';

export function useRecentSearches() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['searches', 'recent'],
    queryFn: async () => getRecentSearches(await getToken()),
  });
}
