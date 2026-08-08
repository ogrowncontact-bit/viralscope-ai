import { apiFetch } from '@/lib/api-client';
import type { Subscription } from '@/features/billing/types';

export function getSubscription(token: string | null): Promise<Subscription> {
  return apiFetch<Subscription>('/api/v1/billing/subscription', { token });
}
