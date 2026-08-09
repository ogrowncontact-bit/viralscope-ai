import { apiFetch } from '@/lib/api-client';

export function createPortalSession(token: string | null): Promise<{ url: string }> {
  return apiFetch<{ url: string }>('/api/v1/billing/portal', { method: 'POST', token });
}
