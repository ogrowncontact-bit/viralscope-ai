import { Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';

export function LoadingSpinner({ className }: { className?: string }) {
  return <Loader2 className={cn('text-muted-foreground size-4 animate-spin', className)} />;
}
