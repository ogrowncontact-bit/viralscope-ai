import { apiFetch } from '@/lib/api-client';

export function removeFavorite(token: string | null, videoId: string): Promise<void> {
  return apiFetch<void>(`/api/v1/favorites/${videoId}`, { method: 'DELETE', token });
}
