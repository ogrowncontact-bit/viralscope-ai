import { apiFetch } from '@/lib/api-client';
import type { SearchResult } from '@/features/searches/types';

export function createSearch(token: string | null, query: string): Promise<SearchResult> {
  return apiFetch<SearchResult>('/api/v1/searches', {
    method: 'POST',
    body: JSON.stringify({ query }),
    token,
  });
}
