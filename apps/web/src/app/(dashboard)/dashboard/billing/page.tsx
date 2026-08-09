import { Suspense } from 'react';

import { ErrorBoundary } from '@/components/states/error-boundary';
import { BillingSkeleton } from '@/features/billing/components/billing-skeleton';
import { BillingView } from '@/features/billing/components/billing-view';

export default function BillingPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Assinatura</h1>
        <p className="text-muted-foreground text-sm">Gerencie seu plano e forma de pagamento.</p>
      </div>

      <ErrorBoundary fallbackTitle="Não foi possível carregar a assinatura">
        <Suspense fallback={<BillingSkeleton />}>
          <BillingView />
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}
