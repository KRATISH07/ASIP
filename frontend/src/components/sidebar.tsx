"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, AlertTriangle, HardHat, Bell,
  BarChart3, Settings, Cpu, Activity, LogOut,
  FileText, Home, Shield,
} from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { incidentsApi, complaintsApi, notificationsApi } from "@/lib/api";

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout, token } = useAuth();

  const [counts, setCounts] = useState({ incidents: 1, complaints: 0, notifications: 0 });

  const fetchCounts = useCallback(async () => {
    if (!token || !user) return;
    let activeIncs = 0, submittedComps = 0, pendingNotes = 0;
    const lastReadIncs = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_incidents") || new Date(0).toISOString()) : new Date(0).toISOString();
    const lastReadComps = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_complaints") || new Date(0).toISOString()) : new Date(0).toISOString();
    const lastReadNotes = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_notifications") || new Date(0).toISOString()) : new Date(0).toISOString();
    try {
      if (user.role === "admin" || user.role === "manager") {
        if (pathname !== "/incidents") {
          try { const incs = await incidentsApi.list(token); const arr = Array.isArray(incs) ? incs : (incs?.items || []); activeIncs = arr.filter((i: any) => { const t = i.updated_at || i.created_at || i.detected_at; return i.status !== "resolved" && t && new Date(t) > new Date(lastReadIncs); }).length; } catch { activeIncs = 1; }
        }
        if (pathname !== "/complaints") {
          try { const c = await complaintsApi.listAll(token); const arr = Array.isArray(c) ? c : (c?.items || []); submittedComps = arr.filter((x: any) => { const t = x.updated_at || x.created_at; return x.status === "submitted" && t && new Date(t) > new Date(lastReadComps); }).length; } catch { submittedComps = 0; }
        }
        if (pathname !== "/notifications") {
          try { const n = await notificationsApi.list(token); const arr = Array.isArray(n) ? n : ((n as any)?.items || []); pendingNotes = arr.filter((x: any) => { const t = x.updated_at || x.created_at; return x.status === "pending" && t && new Date(t) > new Date(lastReadNotes); }).length; } catch { pendingNotes = 0; }
        }
        setCounts({ incidents: activeIncs, complaints: submittedComps, notifications: pendingNotes });
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
    <aside className="w-[260px] bg-gradient-to-b from-[#1e1b4b] to-[#0f172a] flex flex-col h-screen sticky top-0 flex-shrink-0 z-30">
      {/* Logo */}
      <div className="p-5 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-white font-black text-sm shadow-lg shadow-violet-500/30">
          A
        </div>
        <div>
          <h1 className="font-extrabold text-[15px] text-white tracking-tight">ASIP</h1>
          <p className="text-[10px] text-violet-300/70 font-medium">Society Intelligence</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon, badge }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link key={href} href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-semibold transition-all group ${
                active
                  ? "bg-white/10 text-white shadow-sm"
                  : "text-violet-300/60 hover:text-white hover:bg-white/5"
              }`}>
              <Icon className={`w-[18px] h-[18px] ${active ? "text-violet-400" : "text-violet-400/40 group-hover:text-violet-400/80"}`} />
              <span className="flex-1">{label}</span>
              {badge && badge > 0 && (
                <span className="min-w-[20px] h-5 flex items-center justify-center rounded-md text-[10px] font-bold bg-violet-500 text-white px-1.5">
                  {badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="p-4 border-t border-white/5 space-y-3">
        <div className="flex items-center gap-3 px-1">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-[11px] font-bold text-white">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[12px] font-semibold text-white truncate">{user?.full_name || "Demo User"}</p>
            <p className="text-[10px] text-violet-400/60 capitalize">{user?.role || "Admin"}</p>
          </div>
        </div>
        <button onClick={logout}
          className="w-full py-2 rounded-lg text-[12px] font-semibold text-violet-300/50 hover:text-rose-400 hover:bg-rose-500/10 border border-white/5 hover:border-rose-500/20 transition flex items-center justify-center gap-2 cursor-pointer">
          <LogOut className="w-3.5 h-3.5" /> Sign Out
        </button>
      </div>
    </aside>
  );
}
