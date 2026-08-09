import { apiFetch } from '@/lib/api-client';
import type { DashboardStats } from '@/features/stats/types';

export function getDashboardStats(token: string | null): Promise<DashboardStats> {
  return apiFetch<DashboardStats>('/api/v1/dashboard/stats', { token });
}
