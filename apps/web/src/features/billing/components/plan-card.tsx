'use client';

import { Check } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreateCheckoutSession } from '@/features/billing/api/use-create-checkout-session';
import type { Plan } from '@/features/billing/types';

const PLAN_FEATURES: Record<Plan['id'], string[]> = {
  free: ['Buscas limitadas', 'Favoritos ilimitados'],
  pro: ['Buscas ampliadas', 'Análises por IA', 'Transcrição de vídeos'],
  business: ['Tudo do Pro', 'Maior volume de análises', 'Suporte prioritário'],
};

function formatPrice(plan: Plan): string {
  if (plan.id === 'free') return 'Grátis';
  if (plan.price_cents === null || !plan.currency) return 'Preço indisponível';

  const amount = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: plan.currency.toUpperCase(),
  }).format(plan.price_cents / 100);

  return plan.interval ? `${amount}/${plan.interval === 'month' ? 'mês' : plan.interval}` : amount;
}

export function PlanCard({ plan, isCurrent }: { plan: Plan; isCurrent: boolean }) {
  const checkout = useCreateCheckoutSession();
  const canSubscribe = plan.id !== 'free' && !isCurrent && plan.price_cents !== null;

  return (
    <Card className={isCurrent ? 'ring-primary' : undefined}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{plan.name}</CardTitle>
          {isCurrent && <Badge>Plano atual</Badge>}
        </div>
        <p className="text-2xl font-semibold">{formatPrice(plan)}</p>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 text-sm">
          {PLAN_FEATURES[plan.id].map((feature) => (
            <li key={feature} className="flex items-center gap-2">
              <Check className="text-primary size-4" />
              {feature}
            </li>
          ))}
        </ul>
      </CardContent>
      {plan.id !== 'free' && (
        <CardFooter>
          <Button
            className="w-full"
            disabled={!canSubscribe || checkout.isPending}
            onClick={() => checkout.mutate(plan.id)}
          >
            {isCurrent ? 'Plano atual' : 'Assinar'}
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}
