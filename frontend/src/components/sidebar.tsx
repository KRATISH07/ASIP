"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  AlertTriangle,
  HardHat,
  Bell,
  BarChart3,
  Settings,
  Cpu,
  Activity,
  LogOut,
  FileText,
  Building2,
  ShieldCheck,
} from "lucide-react";

import { useAuth } from "@/components/auth-provider";
import { Home } from "lucide-react";
import { incidentsApi, complaintsApi, notificationsApi } from "@/lib/api";

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout, token } = useAuth();

  const [counts, setCounts] = useState({
    incidents: 1,
    complaints: 0,
    notifications: 0,
    myComplaints: 0,
  });

  const fetchCounts = useCallback(async () => {
    if (!token || !user) return;
    
    let activeIncs = 0;
    let submittedComps = 0;
    let pendingNotes = 0;

    const lastReadIncs = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_incidents") || new Date(0).toISOString()) : new Date(0).toISOString();
    const lastReadComps = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_complaints") || new Date(0).toISOString()) : new Date(0).toISOString();
    const lastReadNotes = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_notifications") || new Date(0).toISOString()) : new Date(0).toISOString();

    const viewingIncs = pathname === "/incidents";
    const viewingComps = pathname === "/complaints";
    const viewingNotes = pathname === "/notifications";

    try {
      if (user.role === "admin" || user.role === "manager") {
        if (!viewingIncs) {
          try {
            const incs = await incidentsApi.list(token);
            const incsArray = Array.isArray(incs) ? incs : (incs?.items || []);
            activeIncs = incsArray.filter((i: any) => {
              const itemTime = i.updated_at || i.created_at || i.detected_at;
              return i.status !== "resolved" && itemTime && new Date(itemTime) > new Date(lastReadIncs);
            }).length;
          } catch (e) {
            activeIncs = 1;
          }
        }

        if (!viewingComps) {
          try {
            const compsRes = await complaintsApi.listAll(token);
            const compsArray = Array.isArray(compsRes) ? compsRes : (compsRes?.items || []);
            submittedComps = compsArray.filter((c: any) => {
              const itemTime = c.updated_at || c.created_at;
              return c.status === "submitted" && itemTime && new Date(itemTime) > new Date(lastReadComps);
            }).length;
          } catch (e) {
            submittedComps = 0;
          }
        }

        if (!viewingNotes) {
          try {
            const notes = await notificationsApi.list(token);
            const notesArray = Array.isArray(notes) ? notes : ((notes as any)?.items || []);
            pendingNotes = notesArray.filter((n: any) => {
              const itemTime = n.updated_at || n.created_at;
              return n.status === "pending" && itemTime && new Date(itemTime) > new Date(lastReadNotes);
            }).length;
          } catch (e) {
            pendingNotes = 0;
          }
        }

        setCounts({
          incidents: activeIncs,
          complaints: submittedComps,
          notifications: pendingNotes,
          myComplaints: 0,
        });
      }
    } catch (err) {
      console.warn("Error fetching badge counts:", err);
    }
  }, [token, user, pathname]);

  useEffect(() => {
    fetchCounts();
    const interval = setInterval(fetchCounts, 15000);
    return () => clearInterval(interval);
  }, [fetchCounts]);

  const navItems = [
    { href: "/", label: "Society Operations", icon: LayoutDashboard },
    { href: "/incidents", label: "Incident Triage", icon: AlertTriangle, badge: counts.incidents },
    { href: "/complaints", label: "Resident Complaints", icon: FileText, badge: counts.complaints },
    { href: "/contractors", label: "Ranked Contractors", icon: HardHat },
    { href: "/notifications", label: "Broadcast Alerts", icon: Bell, badge: counts.notifications },
    { href: "/residence", label: "Resident Portal", icon: Home },
    { href: "/sensor-buffer", label: "IoT Edge Gateway", icon: Cpu },
    { href: "/analytics", label: "AI Analytics & Rubric", icon: BarChart3 },
    { href: "/agent-logs", label: "Agent Live Logs", icon: Activity },
    { href: "/settings", label: "Society Settings", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#1c1917] border-r border-[#2d2825] flex flex-col h-screen sticky top-0 flex-shrink-0 z-30 shadow-2xl">
      {/* Brand Header */}
      <div className="p-5 border-b border-[#2d2825] flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-amber-500 to-yellow-600 flex items-center justify-center text-white shadow-lg shadow-amber-900/30 flex-shrink-0">
          <Building2 className="w-5 h-5" />
        </div>
        <div>
          <h1 className="font-extrabold text-sm text-white tracking-tight flex items-center gap-1">
            ASIP <span className="px-1.5 py-0.5 rounded text-[9px] font-black bg-amber-500/20 text-amber-400 border border-amber-500/30">PRO</span>
          </h1>
          <p className="text-[10px] text-stone-400 font-medium truncate">Society AI Operations</p>
        </div>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon, badge }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-2xl text-xs font-bold transition-all duration-200 group ${
                active
                  ? "bg-gradient-to-r from-amber-500/20 to-amber-600/10 text-amber-300 border border-amber-500/30 shadow-sm"
                  : "text-stone-400 hover:text-amber-100 hover:bg-white/5"
              }`}
            >
              <Icon
                className={`w-4 h-4 flex-shrink-0 transition-colors ${
                  active ? "text-amber-400" : "text-stone-500 group-hover:text-amber-200"
                }`}
              />
              <span className="flex-1 truncate">{label}</span>
              
              {badge && badge > 0 ? (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  {badge}
                </span>
              ) : null}

              {active && (
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shadow-xs shadow-amber-400" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User Footer */}
      <div className="p-4 border-t border-[#2d2825] bg-[#141211] flex flex-col gap-3">
        <div className="flex items-center gap-3 px-1">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500 to-yellow-600 flex items-center justify-center text-xs font-extrabold text-white flex-shrink-0">
            {user?.full_name?.charAt(0) || "A"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold text-stone-200 truncate">{user?.full_name || "Society Administrator"}</p>
            <p className="text-[10px] text-amber-400 font-semibold truncate capitalize">{user?.role || "Admin"}</p>
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full py-2 px-3 rounded-xl border border-stone-800 hover:border-rose-500/30 hover:bg-rose-500/10 text-xs font-bold text-stone-400 hover:text-rose-400 transition duration-200 flex items-center justify-center gap-2 cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
