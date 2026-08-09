'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect } from 'react';
import { toast } from 'sonner';

import { ErrorState } from '@/components/states/error-state';
import { BillingSkeleton } from '@/features/billing/components/billing-skeleton';
import { CurrentPlanCard } from '@/features/billing/components/current-plan-card';
import { PlanCard } from '@/features/billing/components/plan-card';
import { usePlans } from '@/features/billing/api/use-plans';
import { useSubscription } from '@/features/billing/api/use-subscription';

export function BillingView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const checkoutResult = searchParams.get('checkout');

  const subscription = useSubscription();
  const plans = usePlans();

  useEffect(() => {
    if (checkoutResult === 'success') {
      toast.success('Assinatura confirmada! Pode levar alguns instantes para atualizar.');
      router.replace('/dashboard/billing');
    } else if (checkoutResult === 'cancel') {
      toast.info('Checkout cancelado — nenhuma cobrança foi feita.');
      router.replace('/dashboard/billing');
    }
  }, [checkoutResult, router]);

  const isPending = subscription.isPending || plans.isPending;
  const isError = subscription.isError || plans.isError;

  if (isPending) return <BillingSkeleton />;

  if (isError) {
    return (
      <ErrorState
        message={subscription.error?.message ?? plans.error?.message ?? 'Erro desconhecido'}
        onRetry={() => {
          void subscription.refetch();
          void plans.refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      <CurrentPlanCard subscription={subscription.data} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {plans.data.map((plan) => (
          <PlanCard key={plan.id} plan={plan} isCurrent={plan.id === subscription.data.plan} />
        ))}
      </div>
    </div>
  );
}
