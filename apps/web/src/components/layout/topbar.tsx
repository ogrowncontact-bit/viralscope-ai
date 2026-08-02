"use client";

import { Menu, Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { SidebarNav } from "@/components/layout/sidebar-nav";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { UserMenu } from "@/components/layout/user-menu";

export function Topbar() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <header className="bg-background/80 sticky top-0 z-10 flex h-14 items-center justify-between gap-4 border-b px-4 backdrop-blur">
      <div className="flex items-center gap-2 md:hidden">
        <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
          <SheetTrigger
            render={<Button variant="ghost" size="icon" aria-label="Abrir menu" />}
          >
            <Menu className="size-5" />
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <SheetHeader className="h-14 flex-row items-center gap-2 border-b px-4">
              <Sparkles className="text-primary size-5" />
              <SheetTitle className="text-sm font-semibold">ViralScope AI</SheetTitle>
            </SheetHeader>
            <div className="p-3" onClick={() => setMobileNavOpen(false)}>
              <SidebarNav />
            </div>
          </SheetContent>
        </Sheet>
      </div>

      <div className="flex-1" />

      <div className="flex items-center gap-2">
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  );
}
