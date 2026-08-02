"use client";

import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useHealth } from "@/features/health/api/use-health";

export function HealthStatusCard() {
  const { data, isPending, isError, error } = useHealth();

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Status da plataforma</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isPending && (
          <div className="space-y-2">
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-1/3" />
          </div>
        )}

        {isError && (
          <div className="flex items-center gap-2 text-sm text-destructive">
            <AlertTriangle className="size-4" />
            <span>Não foi possível conectar à API: {error.message}</span>
          </div>
        )}

        {data && (
          <dl className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">API</dt>
              <dd>
                <Badge variant={data.status === "healthy" ? "default" : "destructive"}>
                  <CheckCircle2 className="size-3" />
                  {data.status}
                </Badge>
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">Banco de dados</dt>
              <dd>{data.database}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-muted-foreground">Ambiente</dt>
              <dd>{data.environment}</dd>
            </div>
          </dl>
        )}
      </CardContent>
    </Card>
  );
}
