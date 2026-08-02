import Link from "next/link";
import { Sparkles } from "lucide-react";

import { SidebarNav } from "@/components/layout/sidebar-nav";

export function Sidebar() {
  return (
    <aside className="bg-sidebar text-sidebar-foreground hidden w-60 shrink-0 flex-col border-r md:flex">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <Sparkles className="text-primary size-5" />
        <Link href="/dashboard" className="text-sm font-semibold tracking-tight">
          ViralScope AI
        </Link>
      </div>
      <div className="flex-1 overflow-y-auto p-3">
        <SidebarNav />
      </div>
    </aside>
  );
}
