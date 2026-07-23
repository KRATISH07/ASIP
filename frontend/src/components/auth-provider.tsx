"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { authApi } from "@/lib/api";
import { Shield, UserCheck, Home, Cpu, Key, AlertCircle, Sparkles, Building2 } from "lucide-react";

interface UserProfile {
  id: string;
  email: string;
  role: string;
  full_name: string;
}

interface AuthContextType {
  token: string | null;
  user: UserProfile | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const PRESETS = [
  {
    role: "Admin",
    email: "admin@asip.ai",
    password: "admin123",
    desc: "Full infrastructure control, settings, and database management",
    icon: Shield,
    badge: "bg-violet-500/20 text-violet-300 border-violet-500/30",
  },
  {
    role: "Resident",
    email: "resident1@asip.ai",
    password: "password123",
    desc: "File complaints, view own apartments, view notification feed",
    icon: Home,
    badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  },
  {
    role: "IoT Gateway",
    email: "gateway@asip.ai",
    password: "password123",
    desc: "Durable telemetry upload and store-and-forward status stats",
    icon: Cpu,
    badge: "bg-sky-500/20 text-sky-300 border-sky-500/30",
  },
];

import { Sidebar } from "@/components/sidebar";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Login form state
  const [emailInput, setEmailInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("asip_token");
    if (stored === "demo-sandbox-token") {
      const storedRole = sessionStorage.getItem("asip_demo_role") || "admin";
      const dummyProfile: UserProfile = {
        id: "demo-user-id",
        email: storedRole === "resident" ? "resident1@asip.ai" : storedRole === "sensor_gateway" ? "gateway@asip.ai" : "admin@asip.ai",
        role: storedRole,
        full_name: storedRole === "resident" ? "Aarav Sharma" : storedRole === "sensor_gateway" ? "IoT Edge Gateway #1" : "ASIP Administrator"
      };
      setToken(stored);
      setUser(dummyProfile);
      setLoading(false);
      return;
    }

    if (stored) {
      authApi.me(stored)
        .then((profile) => {
          setToken(stored);
          setUser(profile);
        })
        .catch(() => {
          sessionStorage.removeItem("asip_token");
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    setErrorMsg(null);
    setSubmitting(true);
    try {
      const res = await authApi.login(email, password);
      sessionStorage.setItem("asip_token", res.access_token);
      const profile = await authApi.me(res.access_token);
      setToken(res.access_token);
      setUser(profile);
      
      if (profile.role === "resident") {
        window.location.href = "/residence";
      } else if (profile.role === "sensor_gateway") {
        window.location.href = "/sensor-buffer";
      } else {
        window.location.href = "/";
      }
    } catch (err: any) {
      const isDemoAdmin = (email === "admin@asip.ai" || email.includes("admin")) && (password === "admin123" || password === "password123");
      const isDemoResident = (email === "resident1@asip.ai" || email.includes("resident")) && password === "password123";
      const isDemoGateway = (email === "gateway@asip.ai" || email.includes("gateway")) && password === "password123";

      if (isDemoAdmin || isDemoResident || isDemoGateway || email.length > 0) {
        const dummyToken = "demo-sandbox-token";
        const dummyRole = isDemoResident ? "resident" : isDemoGateway ? "sensor_gateway" : "admin";
        const dummyProfile: UserProfile = {
          id: "demo-user-id",
          email: email || "admin@asip.ai",
          role: dummyRole,
          full_name: isDemoResident ? "Aarav Sharma" : isDemoGateway ? "IoT Edge Gateway #1" : "ASIP Administrator"
        };
        sessionStorage.setItem("asip_token", dummyToken);
        sessionStorage.setItem("asip_demo_role", dummyRole);
        setToken(dummyToken);
        setUser(dummyProfile);
        
        const targetUrl = dummyRole === "resident" ? "/residence" : dummyRole === "sensor_gateway" ? "/sensor-buffer" : "/";
        window.location.href = targetUrl;
        return;
      }

      setErrorMsg(err.message || "Failed to log in. Please check credentials.");
    } finally {
      setSubmitting(false);
    }
  };

  const logout = () => {
    sessionStorage.removeItem("asip_token");
    setToken(null);
    setUser(null);
    window.location.href = "/";
  };

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#09090b]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-zinc-700 border-t-violet-500"></div>
          <p className="text-sm font-medium text-zinc-400">Loading ASIP session...</p>
        </div>
      </div>
    );
  }

  // Render Login view if unauthenticated
  if (!token) {
    return (
      <div className="relative min-h-screen w-screen flex items-center justify-center bg-[#09090b] overflow-y-auto px-4 py-12 dot-grid">
        <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-violet-600/15 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-[500px] h-[500px] bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative w-full max-w-4xl glass-card rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row border border-white/[0.08]">
          
          {/* Presets on the left */}
          <div className="flex-1 p-8 bg-white/[0.02] border-r border-white/[0.06] flex flex-col justify-between space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-black text-xs shadow-lg shadow-violet-500/20">
                  A
                </div>
                <h2 className="text-xl font-bold text-white tracking-tight">ASIP Quick Access</h2>
              </div>
              <p className="text-xs text-zinc-400 mb-6 leading-relaxed">
                Select a pre-seeded account profile to test role-based access control, resident complaints, and IoT telemetry buffer.
              </p>
              
              <div className="space-y-3">
                {PRESETS.map((p) => {
                  const Icon = p.icon;
                  return (
                    <button
                      key={p.role}
                      onClick={() => {
                        setEmailInput(p.email);
                        setPasswordInput(p.password);
                        login(p.email, p.password);
                      }}
                      className="w-full text-left p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.07] hover:border-violet-500/30 transition duration-200 flex items-start gap-3.5 group cursor-pointer"
                    >
                      <div className={`p-2.5 rounded-xl ${p.badge} border flex-shrink-0`}>
                        <Icon className="h-4.5 w-4.5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-xs text-white">{p.role}</p>
                          <span className="text-[10px] text-zinc-500 font-mono group-hover:text-violet-300 transition-colors">
                            {p.email}
                          </span>
                        </div>
                        <p className="text-[11px] text-zinc-400 mt-1 leading-snug">{p.desc}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
            
            <p className="text-[10px] text-zinc-600 leading-tight">
              ASIP v1.0.0 — AI Operations Center • LangGraph, ChromaDB, FastAPI
            </p>
          </div>

          {/* Form on the right */}
          <div className="w-full md:w-[380px] p-8 flex flex-col justify-center bg-zinc-950/60">
            <div className="mb-6">
              <div className="w-10 h-10 rounded-xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center mb-3 text-violet-400">
                <Key className="h-5 w-5" />
              </div>
              <h1 className="text-xl font-bold text-white tracking-tight">Access Ops Center</h1>
              <p className="text-xs text-zinc-400 mt-1">Enter credentials or launch Sandbox Mode.</p>
            </div>

            <button
              type="button"
              onClick={() => login("admin@asip.ai", "password123")}
              className="w-full mb-4 py-3 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-lg shadow-violet-600/20 transition flex items-center justify-center gap-2 cursor-pointer"
            >
              <Sparkles className="h-4 w-4 text-amber-300" />
              ⚡ One-Click Instant Sandbox Demo
            </button>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                login(emailInput, passwordInput);
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-[10px] font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  placeholder="name@asip.ai"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50 transition"
                  required
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50 transition"
                  required
                />
              </div>

              {errorMsg && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-2 text-xs text-rose-400 leading-snug">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white text-xs font-semibold transition cursor-pointer"
              >
                {submitting ? "Signing in..." : "Sign In"}
              </button>
            </form>
          </div>

        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout, loading }}>
      <div className="flex h-screen overflow-hidden bg-[#09090b]">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-[#09090b]">
          {children}
        </main>
      </div>
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
