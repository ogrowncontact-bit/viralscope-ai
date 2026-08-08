import { Skeleton } from '@/components/ui/skeleton';

export function BillingSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-32 w-full" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-64 w-full" />
        ))}
      </div>
    </div>
  );
}
