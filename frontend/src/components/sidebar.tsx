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
} from "lucide-react";

import { useAuth } from "@/components/auth-provider";
import { Home } from "lucide-react";
import { incidentsApi, complaintsApi, notificationsApi } from "@/lib/api";

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout, token } = useAuth();

  const [counts, setCounts] = useState({
    incidents: 0,
    complaints: 0,
    notifications: 0,
    myComplaints: 0,
  });

  const fetchCounts = useCallback(async () => {
    if (!token || !user) return;
    
    let activeIncs = 0;
    let submittedComps = 0;
    let pendingNotes = 0;
    let activeMine = 0;

    // Get last read timestamps from sessionStorage (default to Unix epoch)
    const lastReadIncs = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_incidents") || new Date(0).toISOString()) : new Date(0).toISOString();
    const lastReadComps = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_complaints") || new Date(0).toISOString()) : new Date(0).toISOString();
    const lastReadNotes = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_notifications") || new Date(0).toISOString()) : new Date(0).toISOString();
    const lastReadRes = typeof window !== "undefined" ? (sessionStorage.getItem("asip_last_read_residence") || new Date(0).toISOString()) : new Date(0).toISOString();

    const viewingIncs = pathname === "/incidents";
    const viewingComps = pathname === "/complaints";
    const viewingNotes = pathname === "/notifications";
    const viewingRes = pathname === "/residence";

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
            console.warn("Failed to fetch incidents count", e);
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
            console.warn("Failed to fetch complaints count", e);
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
            console.warn("Failed to fetch notifications count", e);
          }
        }

        setCounts({
          incidents: activeIncs,
          complaints: submittedComps,
          notifications: pendingNotes,
          myComplaints: 0,
        });
      } else if (user.role === "resident") {
        if (!viewingRes) {
          try {
            const mine = await complaintsApi.listMine(token);
            const mineArray = Array.isArray(mine) ? mine : (mine?.items || []);
            
            let incsArray: any[] = [];
            try {
              const incs = await incidentsApi.list(token);
              incsArray = Array.isArray(incs) ? incs : (incs?.items || []);
            } catch (e) {
              console.warn("Failed to fetch incidents list for resident checks", e);
            }

            activeMine = mineArray.filter((c: any) => {
              const compTime = c.updated_at || c.created_at;
              let maxTime = new Date(compTime);

              if (c.linked_incident_id) {
                const linkedInc = incsArray.find((i: any) => i.id === c.linked_incident_id);
                if (linkedInc) {
                  const incTime = linkedInc.updated_at || linkedInc.created_at || linkedInc.detected_at;
                  if (incTime && new Date(incTime) > maxTime) {
                    maxTime = new Date(incTime);
                  }
                }
              }

              return c.status !== "resolved" && c.status !== "rejected" && maxTime > new Date(lastReadRes);
            }).length;
          } catch (e) {
            console.warn("Failed to fetch resident complaints count", e);
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
            console.warn("Failed to fetch resident notifications count", e);
          }
        }

        setCounts({
          incidents: 0,
          complaints: 0,
          notifications: pendingNotes,
          myComplaints: activeMine,
        });
      }
    } catch (err) {
      console.warn("General failure in sidebar counts processing", err);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, user]);

  useEffect(() => {
    if (!token || !user) {
      setCounts({ incidents: 0, complaints: 0, notifications: 0, myComplaints: 0 });
      return;
    }
    fetchCounts();
    const interval = setInterval(fetchCounts, 8000);
    return () => clearInterval(interval);
  }, [token, user, fetchCounts]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const nowStr = new Date().toISOString();
    if (pathname === "/incidents") {
      sessionStorage.setItem("asip_last_read_incidents", nowStr);
    } else if (pathname === "/complaints") {
      sessionStorage.setItem("asip_last_read_complaints", nowStr);
    } else if (pathname === "/notifications") {
      sessionStorage.setItem("asip_last_read_notifications", nowStr);
    } else if (pathname === "/residence") {
      sessionStorage.setItem("asip_last_read_residence", nowStr);
    }
    fetchCounts();
  }, [pathname, fetchCounts]);

  // Define navigation lists based on user role
  let navItems = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard },
    { href: "/incidents", label: "Incidents", icon: AlertTriangle },
    { href: "/complaints", label: "Complaints", icon: FileText },
    { href: "/contractors", label: "Contractors", icon: HardHat },
    { href: "/notifications", label: "Notifications", icon: Bell },
    { href: "/analytics", label: "Analytics", icon: BarChart3 },
    { href: "/agent-logs", label: "Agent Logs", icon: Cpu },
    { href: "/settings", label: "Settings", icon: Settings },
  ];

  if (user?.role === "resident") {
    navItems = [
      { href: "/residence", label: "Resident Portal", icon: Home },
      { href: "/notifications", label: "My Notifications", icon: Bell },
    ];
  } else if (user?.role === "sensor_gateway") {
    navItems = [
      { href: "/sensor-buffer", label: "Sensor Buffer Stats", icon: Cpu },
    ];
  }

  const itemsWithBadges = navItems.map((item) => {
    let badgeCount = 0;
    if (item.href === "/" || item.href === "/incidents") {
      badgeCount = counts.incidents;
    } else if (item.href === "/complaints") {
      badgeCount = counts.complaints;
    } else if (item.href === "/notifications") {
      badgeCount = counts.notifications;
    } else if (item.href === "/residence") {
      badgeCount = counts.myComplaints;
    }
    return { ...item, badge: badgeCount };
  });

  return (
    <aside className="w-64 flex-shrink-0 bg-[#2c2418] border-r border-[#3d3425] flex flex-col">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-[#3d3425]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500 to-yellow-600 flex items-center justify-center shadow-lg shadow-amber-500/20">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-sm text-amber-50 tracking-tight">ASIP</p>
            <p className="text-[10px] text-stone-400 leading-tight">AI Ops Center</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {itemsWithBadges.map(({ href, label, icon: Icon, badge }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
                active
                  ? "bg-amber-500/15 text-amber-300 border border-amber-500/25"
                  : "text-stone-400 hover:text-amber-100 hover:bg-white/5"
              }`}
            >
              <Icon
                className={`w-4.5 h-4.5 flex-shrink-0 transition-colors ${
                  active ? "text-amber-400" : "text-stone-500 group-hover:text-stone-300"
                }`}
                size={18}
              />
              <span className="flex-1 truncate">{label}</span>
              
              {/* Badge "num pop" */}
              {badge > 0 && !active && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold tracking-tight bg-amber-500/20 text-amber-300 group-hover:bg-amber-500/30 group-hover:text-amber-200 transition-colors">
                  {badge}
                </span>
              )}

              {active && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-amber-400" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-[#3d3425] flex flex-col gap-3">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500 to-orange-400 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-amber-50 truncate">{user?.full_name || "User"}</p>
            <p className="text-[10px] text-stone-400 truncate capitalize">{user?.role || "Resident"}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full py-2 px-3 rounded-xl border border-[#3d3425] hover:border-rose-500/30 hover:bg-rose-500/10 text-xs font-medium text-stone-400 hover:text-rose-400 transition duration-200"
        >
          Sign Out
        </button>
      </div>
    </aside>
  );
}
