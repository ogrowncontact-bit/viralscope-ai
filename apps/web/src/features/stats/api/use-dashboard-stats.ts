import { useAuth } from '@clerk/nextjs';
import { useQuery } from '@tanstack/react-query';

import { getDashboardStats } from '@/features/stats/api/get-dashboard-stats';

export function useDashboardStats() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => getDashboardStats(await getToken()),
  });
}
