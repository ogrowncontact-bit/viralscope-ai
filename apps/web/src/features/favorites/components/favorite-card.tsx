"use client";

import { Heart, Video as VideoIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { FavoriteVideo } from "@/features/favorites/types";
import { useRemoveFavorite } from "@/features/favorites/api/use-remove-favorite";

export function FavoriteCard({ favorite }: { favorite: FavoriteVideo }) {
  const removeFavorite = useRemoveFavorite();

  return (
    <Card className="overflow-hidden py-0">
      <div className="bg-muted flex aspect-video items-center justify-center">
        {favorite.thumbnail_url ? (
          // eslint-disable-next-line @next/next/no-img-element -- thumbnails vêm de domínios externos do YouTube
          <img
            src={favorite.thumbnail_url}
            alt={favorite.title}
            className="size-full object-cover"
          />
        ) : (
          <VideoIcon className="text-muted-foreground size-8" />
        )}
      </div>
      <CardContent className="space-y-2 py-4">
        <p className="line-clamp-2 text-sm font-medium">{favorite.title}</p>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground text-xs">{favorite.channel_title}</span>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Remover dos favoritos"
            disabled={removeFavorite.isPending}
            onClick={() => removeFavorite.mutate(favorite.video_id)}
          >
            <Heart className="fill-primary text-primary size-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
