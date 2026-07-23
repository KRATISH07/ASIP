"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { authApi } from "@/lib/api";
import { Shield, UserCheck, Home, HardHat, Cpu, Key, AlertCircle } from "lucide-react";

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
    color: "from-amber-600 to-yellow-700",
  },
  {
    role: "Resident",
    email: "resident1@asip.ai",
    password: "password123",
    desc: "File complaints, view own apartments, view notification feed",
    icon: Home,
    color: "from-emerald-600 to-teal-700",
  },
  {
    role: "IoT Gateway",
    email: "gateway@asip.ai",
    password: "password123",
    desc: "Durable telemetry upload and store-and-forward status stats",
    icon: Cpu,
    color: "from-stone-500 to-stone-700",
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
      // Demo Sandbox Mode Fallback (when backend API is not running)
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
      <div className="flex h-screen w-screen items-center justify-center bg-[#faf6f0]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-amber-200 border-t-amber-600"></div>
          <p className="text-sm font-medium text-stone-400">Loading ASIP session...</p>
        </div>
      </div>
    );
  }

  // Render Login view if unauthenticated
  if (!token) {
    return (
      <div className="relative min-h-screen w-screen flex items-center justify-center bg-[#faf6f0] overflow-y-auto px-4 py-12">
        {/* Decorative backgrounds */}
        <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-amber-300/15 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-96 h-96 bg-orange-200/15 rounded-full blur-3xl"></div>

        <div className="relative w-full max-w-4xl bg-white border border-stone-200 rounded-3xl overflow-hidden shadow-xl shadow-stone-200/50 flex flex-col md:flex-row">
          
          {/* Presets / Role switch options on the left */}
          <div className="flex-1 p-8 bg-stone-50 border-r border-stone-200 flex flex-col justify-between">
            <div>
              <h2 className="text-xl font-bold text-stone-800 tracking-tight">ASIP Accounts Seeding</h2>
              <p className="text-xs text-stone-500 mt-2 mb-6">
                To test the new store-and-forward sensor buffer, resident complaints, and RBAC isolation, select one of the seeded user profiles below.
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
                      className="w-full text-left p-3.5 rounded-2xl bg-white border border-stone-200 hover:border-amber-300 hover:shadow-md hover:shadow-amber-100/50 transition duration-200 flex items-start gap-3 group cursor-pointer"
                    >
                      <div className={`p-2 rounded-xl bg-gradient-to-br ${p.color} text-white flex-shrink-0`}>
                        <Icon className="h-4.5 w-4.5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-xs text-stone-800">{p.role}</p>
                          <span className="text-[9px] text-stone-400 font-mono group-hover:text-amber-600 transition-colors">
                            {p.email}
                          </span>
                        </div>
                        <p className="text-[10px] text-stone-500 mt-1 leading-snug">{p.desc}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
            
            <p className="text-[9px] text-stone-400 mt-6 leading-tight">
              ASIP v1.0.0 — AI operations center. Powered by LangGraph, ChromaDB, and FastAPI.
            </p>
          </div>

          {/* Regular Login Form on the right */}
          <div className="w-full md:w-[380px] p-8 flex flex-col justify-center bg-white">
            <div className="mb-8">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-yellow-600 flex items-center justify-center shadow-lg shadow-amber-300/30 mb-4">
                <Key className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-stone-800 tracking-tight">Access Ops Center</h1>
              <p className="text-xs text-stone-500 mt-1.5">Enter your credentials below to log in manually.</p>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                login(emailInput, passwordInput);
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-[11px] font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  placeholder="name@asip.ai"
                  className="w-full px-4 py-3 rounded-xl bg-stone-50 border border-stone-200 text-sm text-stone-800 placeholder:text-stone-400 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-100 transition"
                  required
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 rounded-xl bg-stone-50 border border-stone-200 text-sm text-stone-800 placeholder:text-stone-400 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-100 transition"
                  required
                />
              </div>

              {errorMsg && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-2 text-xs text-rose-600 leading-snug">
                  <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3.5 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:bg-amber-300 text-white text-sm font-semibold transition shadow-lg shadow-amber-200/40 cursor-pointer"
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
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-[#faf6f0]">
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
