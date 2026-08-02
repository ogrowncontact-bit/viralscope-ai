import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { removeFavorite } from "@/features/favorites/api/remove-favorite";

export function useRemoveFavorite() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (videoId: string) => removeFavorite(await getToken(), videoId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["favorites"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard", "stats"] });
    },
  });
}
