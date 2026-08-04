'use client';

import { Search as SearchIcon } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useCreateSearch } from '@/features/searches/api/use-create-search';
import { SearchResults } from '@/features/searches/components/search-results';
import type { Video } from '@/features/searches/types';

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Video[] | null>(null);
  const createSearch = useCreateSearch();

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;

    createSearch.mutate(trimmed, {
      onSuccess: (data) => {
        setResults(data.videos);
        setQuery('');
      },
      onError: () => {
        toast.error('Não foi possível registrar a busca. Tente de novo.');
      },
    });
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <SearchIcon className="text-muted-foreground absolute top-1/2 left-3 size-4 -translate-y-1/2" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar vídeos, canais ou assuntos em alta…"
            className="pl-9"
          />
        </div>
        <Button type="submit" disabled={createSearch.isPending || !query.trim()}>
          Buscar
        </Button>
      </form>

      {results && <SearchResults videos={results} />}
    </div>
  );
}
