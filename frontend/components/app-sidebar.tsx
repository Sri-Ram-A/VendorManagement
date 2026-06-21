"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Building2, ShieldCheck, Settings } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

const navItems = [
  { title: "Portfolio Overview", url: "/", icon: LayoutDashboard },
  { title: "Third-Party Ledger", url: "/vendors", icon: Building2 },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar className="border-r border-border rounded-none" variant="sidebar" collapsible="icon">
      <SidebarHeader className="border-b border-border py-4 px-4 flex flex-row items-center gap-2">
        <ShieldCheck className="h-5 w-5 text-sky-500 shrink-0" />
        <span className="font-sans font-bold tracking-tight text-sm text-foreground uppercase truncate group-data-[collapsible=icon]:hidden">
          Vanguard Risk
        </span>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="font-mono text-[10px] tracking-wider uppercase group-data-[collapsible=icon]:hidden">
            Navigation Control
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const isActive = pathname === item.url;
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.title}
                      className="rounded-sm font-sans"
                    >
                      <Link href={item.url} className="flex items-center gap-3">
                        <item.icon size={16} className={isActive ? "text-sky-500" : "text-muted-foreground"} />
                        <span className="text-sm font-medium">{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}