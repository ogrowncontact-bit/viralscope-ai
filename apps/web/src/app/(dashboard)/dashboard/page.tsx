import { ErrorBoundary } from "@/components/states/error-boundary";
import { FavoritesGrid } from "@/features/favorites/components/favorites-grid";
import { RecentSearchesList } from "@/features/searches/components/recent-searches-list";
import { SearchBar } from "@/features/searches/components/search-bar";
import { StatsCards } from "@/features/stats/components/stats-cards";

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground text-sm">
          Acompanhe tendências e o que você já pesquisou.
        </p>
      </div>

      <ErrorBoundary fallbackTitle="Não foi possível carregar as estatísticas">
        <StatsCards />
      </ErrorBoundary>

      <ErrorBoundary fallbackTitle="Não foi possível carregar a busca">
        <SearchBar />
      </ErrorBoundary>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <ErrorBoundary fallbackTitle="Não foi possível carregar as pesquisas recentes">
          <RecentSearchesList />
        </ErrorBoundary>
        <ErrorBoundary fallbackTitle="Não foi possível carregar os favoritos">
          <FavoritesGrid />
        </ErrorBoundary>
      </div>
    </div>
  );
}
