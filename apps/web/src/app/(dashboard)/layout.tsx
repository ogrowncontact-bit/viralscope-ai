import { auth } from '@clerk/nextjs/server';
import type { ReactNode } from 'react';

import { DashboardShell } from '@/components/layout/dashboard-shell';

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  await auth.protect();

  return <DashboardShell>{children}</DashboardShell>;
}
