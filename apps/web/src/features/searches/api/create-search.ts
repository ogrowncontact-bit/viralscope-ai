import { apiFetch } from "@/lib/api-client";
import type { Search } from "@/features/searches/types";

export function createSearch(token: string | null, query: string): Promise<Search> {
  return apiFetch<Search>("/api/v1/searches", {
    method: "POST",
    body: JSON.stringify({ query }),
    token,
  });
}
