import { Show } from '@clerk/nextjs';
import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/layout/theme-toggle';

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <header className="flex items-center justify-between border-b px-6 py-4">
        <span className="text-sm font-semibold tracking-tight">ViralScope AI</span>
        <ThemeToggle />
      </header>
      <main className="flex flex-1 flex-col items-center justify-center gap-6 px-6 text-center">
        <h1 className="max-w-xl text-4xl font-semibold tracking-tight text-balance">
          Descubra vídeos com alto potencial de viralização
        </h1>
        <p className="text-muted-foreground max-w-md text-balance">
          Encontre tendências, entenda por que um vídeo viralizou e descubra os melhores títulos e
          hooks — com IA.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Show when="signed-out">
            <Button render={<Link href="/sign-up" />} nativeButton={false}>
              Criar conta
            </Button>
            <Button variant="outline" render={<Link href="/sign-in" />} nativeButton={false}>
              Entrar
            </Button>
          </Show>
          <Show when="signed-in">
            <Button render={<Link href="/dashboard" />} nativeButton={false}>
              Ir para o dashboard
            </Button>
          </Show>
          <Button variant="ghost" render={<Link href="/status" />} nativeButton={false}>
            Ver status da plataforma
          </Button>
        </div>
      </main>
    </div>
  );
}
