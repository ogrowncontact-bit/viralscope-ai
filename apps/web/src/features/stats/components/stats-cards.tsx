"use client";

import { Heart, Search, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { ErrorState } from "@/components/states/error-state";
import { useDashboardStats } from "@/features/stats/api/use-dashboard-stats";
import { StatsSkeleton } from "@/features/stats/components/stats-skeleton";

interface StatDefinition {
  label: string;
  icon: LucideIcon;
  value: (stats: { searches_count: number; favorites_count: number; analyses_count: number }) => number;
}

const STAT_DEFINITIONS: StatDefinition[] = [
  { label: "Pesquisas realizadas", icon: Search, value: (s) => s.searches_count },
  { label: "Vídeos favoritados", icon: Heart, value: (s) => s.favorites_count },
  { label: "Análises geradas", icon: Sparkles, value: (s) => s.analyses_count },
];

export function StatsCards() {
  const { data, isPending, isError, error, refetch } = useDashboardStats();

  if (isPending) return <StatsSkeleton />;

  if (isError) {
    return <ErrorState message={error.message} onRetry={() => void refetch()} />;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {STAT_DEFINITIONS.map(({ label, icon: Icon, value }) => (
        <Card key={label}>
          <CardContent className="flex items-center gap-4 py-4">
            <div className="bg-primary/10 flex size-10 items-center justify-center rounded-full">
              <Icon className="text-primary size-5" />
            </div>
            <div>
              <p className="text-2xl font-semibold tabular-nums">{value(data)}</p>
              <p className="text-muted-foreground text-xs">{label}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
