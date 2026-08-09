import { apiFetch } from '@/lib/api-client';
import type { SubscriptionPlanId } from '@/features/billing/types';

export function createCheckoutSession(
  token: string | null,
  plan: SubscriptionPlanId,
): Promise<{ url: string }> {
  return apiFetch<{ url: string }>('/api/v1/billing/checkout', {
    method: 'POST',
    token,
    body: JSON.stringify({ plan }),
  });
}
