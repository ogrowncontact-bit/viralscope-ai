import { useAuth } from '@clerk/nextjs';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';

import { createPortalSession } from '@/features/billing/api/create-portal-session';

export function useCreatePortalSession() {
  const { getToken } = useAuth();

  return useMutation({
    mutationFn: async () => createPortalSession(await getToken()),
    onSuccess: (data) => {
      window.location.href = data.url;
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });
}
