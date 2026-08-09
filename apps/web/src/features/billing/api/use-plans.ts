import { useQuery } from '@tanstack/react-query';

import { getPlans } from '@/features/billing/api/get-plans';

export function usePlans() {
  return useQuery({
    queryKey: ['billing', 'plans'],
    queryFn: getPlans,
  });
}
