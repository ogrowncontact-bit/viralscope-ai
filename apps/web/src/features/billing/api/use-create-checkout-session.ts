import { useAuth } from '@clerk/nextjs';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';

import { createCheckoutSession } from '@/features/billing/api/create-checkout-session';
import type { SubscriptionPlanId } from '@/features/billing/types';

export function useCreateCheckoutSession() {
  const { getToken } = useAuth();

  return useMutation({
    mutationFn: async (plan: SubscriptionPlanId) => createCheckoutSession(await getToken(), plan),
    onSuccess: (data) => {
      window.location.href = data.url;
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });
}
