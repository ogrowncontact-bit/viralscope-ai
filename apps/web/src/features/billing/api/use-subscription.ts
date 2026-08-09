import { useAuth } from '@clerk/nextjs';
import { useQuery } from '@tanstack/react-query';

import { getSubscription } from '@/features/billing/api/get-subscription';

export function useSubscription() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['billing', 'subscription'],
    queryFn: async () => getSubscription(await getToken()),
  });
}
