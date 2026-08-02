import { Skeleton } from "@/components/ui/skeleton";

export function FavoritesSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {Array.from({ length: 2 }).map((_, i) => (
        <Skeleton key={i} className="aspect-video w-full" />
      ))}
    </div>
  );
}
