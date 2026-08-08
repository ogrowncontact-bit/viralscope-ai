'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreatePortalSession } from '@/features/billing/api/use-create-portal-session';
import type { Subscription } from '@/features/billing/types';

const PLAN_LABELS: Record<Subscription['plan'], string> = {
  free: 'Free',
  pro: 'Pro',
  business: 'Business',
};

const STATUS_LABELS: Record<Subscription['status'], string> = {
  active: 'Ativa',
  trialing: 'Em teste',
  past_due: 'Pagamento pendente',
  canceled: 'Cancelada',
  incomplete: 'Incompleta',
};

export function CurrentPlanCard({ subscription }: { subscription: Subscription }) {
  const portal = useCreatePortalSession();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Seu plano</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold">{PLAN_LABELS[subscription.plan]}</span>
          <Badge variant={subscription.status === 'active' ? 'default' : 'secondary'}>
            {STATUS_LABELS[subscription.status]}
          </Badge>
        </div>

        {subscription.current_period_end && (
          <p className="text-muted-foreground text-sm">
            Renova em {new Date(subscription.current_period_end).toLocaleDateString('pt-BR')}
          </p>
        )}

        {subscription.plan !== 'free' && (
          <Button variant="outline" disabled={portal.isPending} onClick={() => portal.mutate()}>
            Gerenciar assinatura
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
