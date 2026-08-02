"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { navItems } from "@/components/layout/nav-items";
import { cn } from "@/lib/utils";

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-1">
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;

        if (item.comingSoon) {
          return (
            <div
              key={item.href}
              className="text-muted-foreground/60 flex items-center justify-between gap-2 rounded-md px-3 py-2 text-sm"
              aria-disabled
            >
              <span className="flex items-center gap-2">
                <Icon className="size-4" />
                {item.label}
              </span>
              <Badge variant="outline" className="text-[10px]">
                em breve
              </Badge>
            </div>
          );
        }

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )}
          >
            <Icon className="size-4" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
