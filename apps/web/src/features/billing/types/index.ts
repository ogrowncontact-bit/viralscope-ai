export type SubscriptionPlanId = 'free' | 'pro' | 'business';

export type SubscriptionStatus = 'active' | 'trialing' | 'past_due' | 'canceled' | 'incomplete';

export interface Subscription {
  plan: SubscriptionPlanId;
  status: SubscriptionStatus;
  current_period_end: string | null;
}

export interface Plan {
  id: SubscriptionPlanId;
  name: string;
  price_cents: number | null;
  currency: string | null;
  interval: string | null;
}
