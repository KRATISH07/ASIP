"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, AlertTriangle, HardHat, Bell,
  BarChart3, Settings, Cpu, Activity, LogOut,
  FileText, Home,
} from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { incidentsApi, complaintsApi, notificationsApi } from "@/lib/api";

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout, token } = useAuth();
  const [counts, setCounts] = useState({ incidents: 1, complaints: 0, notifications: 0 });

  const fetchCounts = useCallback(async () => {
    if (!token || !user) return;
    let a = 0, b = 0, c = 0;
    const lr1 = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_incidents") || new Date(0).toISOString()) : new Date(0).toISOString();
    const lr2 = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_complaints") || new Date(0).toISOString()) : new Date(0).toISOString();
    const lr3 = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_notifications") || new Date(0).toISOString()) : new Date(0).toISOString();
    try {
      if (user.role === "admin" || user.role === "manager") {
        if (pathname !== "/incidents") { try { const r = await incidentsApi.list(token); const arr = Array.isArray(r) ? r : (r?.items || []); a = arr.filter((i: any) => { const t = i.updated_at || i.created_at || i.detected_at; return i.status !== "resolved" && t && new Date(t) > new Date(lr1); }).length; } catch { a = 1; } }
        if (pathname !== "/complaints") { try { const r = await complaintsApi.listAll(token); const arr = Array.isArray(r) ? r : (r?.items || []); b = arr.filter((x: any) => { const t = x.updated_at || x.created_at; return x.status === "submitted" && t && new Date(t) > new Date(lr2); }).length; } catch { b = 0; } }
        if (pathname !== "/notifications") { try { const r = await notificationsApi.list(token); const arr = Array.isArray(r) ? r : ((r as any)?.items || []); c = arr.filter((x: any) => { const t = x.updated_at || x.created_at; return x.status === "pending" && t && new Date(t) > new Date(lr3); }).length; } catch { c = 0; } }
        setCounts({ incidents: a, complaints: b, notifications: c });
      }
    } catch {}
  }, [token, user, pathname]);

  useEffect(() => { fetchCounts(); const iv = setInterval(fetchCounts, 15000); return () => clearInterval(iv); }, [fetchCounts]);

  let navItems: { href: string; label: string; icon: any; badge?: number }[] = [];
  if (user?.role === "resident") {
    navItems = [
      { href: "/residence", label: "My Apartment", icon: Home },
      { href: "/notifications", label: "Announcements", icon: Bell, badge: counts.notifications },
    ];
  } else if (user?.role === "sensor_gateway") {
    navItems = [{ href: "/sensor-buffer", label: "Telemetry Buffer", icon: Cpu }];
  } else {
    navItems = [
      { href: "/", label: "Dashboard", icon: LayoutDashboard },
      { href: "/incidents", label: "Incidents", icon: AlertTriangle, badge: counts.incidents },
      { href: "/complaints", label: "Complaints", icon: FileText, badge: counts.complaints },
      { href: "/contractors", label: "Contractors", icon: HardHat },
      { href: "/notifications", label: "Alerts", icon: Bell, badge: counts.notifications },
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/agent-logs", label: "Agent Logs", icon: Activity },
      { href: "/settings", label: "Settings", icon: Settings },
    ];
  }

  return (
    <aside className="w-[240px] bg-[#09090b] border-r border-white/[0.06] flex flex-col h-screen sticky top-0 flex-shrink-0 z-30">
      {/* Logo */}
      <div className="px-5 py-5 flex items-center gap-3 border-b border-white/[0.06]">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-black text-xs shadow-lg shadow-violet-500/20">
          A
        </div>
        <div>
          <h1 className="font-bold text-sm text-white tracking-tight">ASIP</h1>
          <p className="text-[10px] text-zinc-500">Operations Center</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2.5 py-3 space-y-0.5 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon, badge }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link key={href} href={href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] transition-all group ${
                active
                  ? "bg-white/[0.08] text-white font-semibold"
                  : "text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.04] font-medium"
              }`}>
              <Icon className={`w-4 h-4 flex-shrink-0 ${active ? "text-violet-400" : "text-zinc-600 group-hover:text-zinc-400"}`} />
              <span className="flex-1">{label}</span>
              {badge && badge > 0 && (
                <span className="min-w-[18px] h-[18px] flex items-center justify-center rounded text-[9px] font-bold bg-violet-500/20 text-violet-400 px-1">
                  {badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="p-3 border-t border-white/[0.06] space-y-2">
        <div className="flex items-center gap-2.5 px-2">
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-[10px] font-bold text-white">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-medium text-zinc-300 truncate">{user?.full_name || "Demo User"}</p>
            <p className="text-[9px] text-zinc-600 capitalize">{user?.role || "Admin"}</p>
          </div>
        </div>
        <button onClick={logout}
          className="w-full py-1.5 rounded-md text-[11px] font-medium text-zinc-600 hover:text-rose-400 hover:bg-rose-500/10 transition flex items-center justify-center gap-1.5 cursor-pointer">
          <LogOut className="w-3 h-3" /> Sign Out
        </button>
      </div>
    </aside>
  );
}
