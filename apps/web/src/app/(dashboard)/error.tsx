'use client';

import { useEffect } from 'react';

import { Button } from '@/components/ui/button';
import { ErrorState } from '@/components/states/error-state';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('[DashboardError]', error);
  }, [error]);

  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <div className="w-full max-w-md space-y-4">
        <ErrorState
          title="Não foi possível carregar o dashboard"
          message={error.message || 'Erro inesperado.'}
        />
        <Button variant="outline" className="w-full" onClick={reset}>
          Tentar novamente
        </Button>
      </div>
    </div>
  );
}
