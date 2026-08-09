import { apiFetch } from '@/lib/api-client';
import type { Search } from '@/features/searches/types';

export function getRecentSearches(token: string | null): Promise<Search[]> {
  return apiFetch<Search[]>('/api/v1/searches/recent', { token });
}
