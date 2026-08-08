import type { LucideIcon } from 'lucide-react';
import { CreditCard, LayoutDashboard, Users } from 'lucide-react';

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  comingSoon?: boolean;
}

export const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Competidores', href: '/dashboard/competitors', icon: Users, comingSoon: true },
  { label: 'Assinatura', href: '/dashboard/billing', icon: CreditCard },
];
