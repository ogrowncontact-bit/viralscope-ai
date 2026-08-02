import { apiFetch } from "@/lib/api-client";
import type { FavoriteVideo } from "@/features/favorites/types";

export function getFavorites(token: string | null): Promise<FavoriteVideo[]> {
  return apiFetch<FavoriteVideo[]>("/api/v1/favorites", { token });
}
