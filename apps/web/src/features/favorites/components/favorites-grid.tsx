'use client';

import { Heart } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/states/empty-state';
import { ErrorState } from '@/components/states/error-state';
import { useFavorites } from '@/features/favorites/api/use-favorites';
import { FavoriteCard } from '@/features/favorites/components/favorite-card';
import { FavoritesSkeleton } from '@/features/favorites/components/favorites-skeleton';

export function FavoritesGrid() {
  const { data, isPending, isError, error, refetch } = useFavorites();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Heart className="size-4" />
          Favoritos
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isPending && <FavoritesSkeleton />}

        {isError && <ErrorState message={error.message} onRetry={() => void refetch()} />}

        {data && data.length === 0 && (
          <EmptyState
            icon={Heart}
            title="Nenhum favorito ainda"
            description="Vídeos favoritados aparecem aqui assim que a descoberta de vídeos estiver disponível."
          />
        )}

        {data && data.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {data.map((favorite) => (
              <FavoriteCard key={favorite.favorite_id} favorite={favorite} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
