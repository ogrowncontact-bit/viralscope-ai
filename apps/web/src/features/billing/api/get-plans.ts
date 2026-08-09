import { apiFetch } from '@/lib/api-client';
import type { Plan } from '@/features/billing/types';

export function getPlans(): Promise<Plan[]> {
  return apiFetch<Plan[]>('/api/v1/billing/plans');
}
