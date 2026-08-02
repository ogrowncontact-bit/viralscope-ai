"use client";

import { History } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { useRecentSearches } from "@/features/searches/api/use-recent-searches";
import { RecentSearchesSkeleton } from "@/features/searches/components/recent-searches-skeleton";

export function RecentSearchesList() {
  const { data, isPending, isError, error, refetch } = useRecentSearches();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="size-4" />
          Pesquisas recentes
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isPending && <RecentSearchesSkeleton />}

        {isError && (
          <ErrorState message={error.message} onRetry={() => void refetch()} />
        )}

        {data && data.length === 0 && (
          <EmptyState
            icon={History}
            title="Nenhuma busca ainda"
            description="Suas pesquisas recentes aparecem aqui."
          />
        )}

        {data && data.length > 0 && (
          <ul className="divide-y">
            {data.map((search) => (
              <li key={search.id} className="flex items-center justify-between py-2 text-sm">
                <span>{search.query}</span>
                <span className="text-muted-foreground text-xs">
                  {new Date(search.created_at).toLocaleString("pt-BR")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
