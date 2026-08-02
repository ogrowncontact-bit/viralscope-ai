import { HealthStatusCard } from "@/features/health/components/health-status-card";

export default function StatusPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-6 p-8">
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight">ViralScope AI</h1>
        <p className="text-muted-foreground text-sm">
          Página de verificação — Módulo 1 (estrutura inicial)
        </p>
      </div>
      <HealthStatusCard />
    </main>
  );
}
