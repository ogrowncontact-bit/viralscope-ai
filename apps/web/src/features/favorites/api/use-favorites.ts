import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { getFavorites } from "@/features/favorites/api/get-favorites";

export function useFavorites() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["favorites"],
    queryFn: async () => getFavorites(await getToken()),
  });
}
