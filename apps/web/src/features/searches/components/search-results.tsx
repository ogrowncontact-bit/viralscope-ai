import { Video as VideoIcon } from 'lucide-react';

import { EmptyState } from '@/components/states/empty-state';
import type { Video } from '@/features/searches/types';
import { VideoResultCard } from '@/features/searches/components/video-result-card';

export function SearchResults({ videos }: { videos: Video[] }) {
  if (videos.length === 0) {
    return (
      <EmptyState
        icon={VideoIcon}
        title="Nenhum vídeo encontrado"
        description="Tente uma busca com outros termos."
      />
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {videos.map((video) => (
        <VideoResultCard key={video.id} video={video} />
      ))}
    </div>
  );
}
