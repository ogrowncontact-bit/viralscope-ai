import { Eye, ThumbsUp, Video as VideoIcon } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import type { Video } from '@/features/searches/types';

function formatDuration(seconds: number | null): string | null {
  if (seconds === null) return null;
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return `${minutes}:${remaining.toString().padStart(2, '0')}`;
}

export function VideoResultCard({ video }: { video: Video }) {
  const duration = formatDuration(video.duration_seconds);

  return (
    <Card className="overflow-hidden py-0">
      <div className="bg-muted relative flex aspect-video items-center justify-center">
        {video.thumbnail_url ? (
          // eslint-disable-next-line @next/next/no-img-element -- thumbnails vêm de domínios externos do YouTube
          <img src={video.thumbnail_url} alt={video.title} className="size-full object-cover" />
        ) : (
          <VideoIcon className="text-muted-foreground size-8" />
        )}
        {duration && (
          <span className="absolute right-1.5 bottom-1.5 rounded bg-black/80 px-1.5 py-0.5 text-xs text-white">
            {duration}
          </span>
        )}
      </div>
      <CardContent className="space-y-2 py-4">
        <p className="line-clamp-2 text-sm font-medium">{video.title}</p>
        <p className="text-muted-foreground truncate text-xs">{video.channel_title}</p>
        <div className="text-muted-foreground flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1">
            <Eye className="size-3.5" />
            {video.view_count.toLocaleString('pt-BR')}
          </span>
          <span className="flex items-center gap-1">
            <ThumbsUp className="size-3.5" />
            {video.like_count.toLocaleString('pt-BR')}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
