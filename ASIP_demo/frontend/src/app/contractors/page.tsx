"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { contractorsApi, type ContractorOut } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import { Star, Clock, Briefcase, Phone, Mail, MapPin, CheckCircle2, Trash2, Plus, X } from "lucide-react";

const MOCK_CONTRACTORS: ContractorOut[] = [
  { id: "1", name: "AquaFix Pro", specializations: ["water", "plumbing"], rating: 4.8, avg_response_time_hrs: 2.0, total_jobs: 145, success_rate: 0.97, contact_info: { phone: "+91-9876543210", email: "aquafix@example.com", address: "Sector 12, Noida" }, is_active: true },
  { id: "2", name: "PowerSure Services", specializations: ["electrical", "power"], rating: 4.6, avg_response_time_hrs: 1.5, total_jobs: 203, success_rate: 0.95, contact_info: { phone: "+91-9123456780", email: "powersure@example.com", address: "Sector 18, Gurugram" }, is_active: true },
  { id: "3", name: "CityFix General", specializations: ["water", "electrical", "civil"], rating: 4.2, avg_response_time_hrs: 3.5, total_jobs: 87, success_rate: 0.89, contact_info: { phone: "+91-9988776655", email: "cityfix@example.com", address: "Sector 5, Delhi" }, is_active: true },
  { id: "4", name: "RapidRepair Elite", specializations: ["water", "electrical"], rating: 4.9, avg_response_time_hrs: 1.0, total_jobs: 312, success_rate: 0.98, contact_info: { phone: "+91-9001234567", email: "rapid@example.com", address: "Sector 62, Noida" }, is_active: true },
  { id: "5", name: "EcoPlumb Budget", specializations: ["water", "plumbing"], rating: 4.0, avg_response_time_hrs: 4.5, total_jobs: 62, success_rate: 0.88, contact_info: { phone: "+91-9871112223", email: "ecoplumb@example.com", address: "Sector 22, Noida" }, is_active: true },
  { id: "6", name: "VoltFlash Emergency", specializations: ["electrical", "power"], rating: 4.7, avg_response_time_hrs: 0.6, total_jobs: 158, success_rate: 0.96, contact_info: { phone: "+91-9873334445", email: "voltflash@example.com", address: "Sector 34, Gurugram" }, is_active: true },
  { id: "7", name: "SureBuild Civil", specializations: ["civil"], rating: 4.9, avg_response_time_hrs: 3.5, total_jobs: 94, success_rate: 0.99, contact_info: { phone: "+91-9875556667", email: "surebuild@example.com", address: "Sector 45, Delhi" }, is_active: true },
  { id: "8", name: "QuickTap Plumbing", specializations: ["water", "plumbing"], rating: 4.5, avg_response_time_hrs: 0.8, total_jobs: 120, success_rate: 0.94, contact_info: { phone: "+91-9877778889", email: "quicktap@example.com", address: "Sector 50, Noida" }, is_active: true },
];

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((s) => (
        <Star key={s} className={`w-3.5 h-3.5 ${s <= Math.round(rating) ? "text-amber-400 fill-amber-400" : "text-zinc-600"}`} />
      ))}
      <span className="text-xs text-zinc-400 ml-1">{rating.toFixed(1)}</span>
    </div>
  );
}

const SPEC_COLORS: Record<string, string> = {
  water: "bg-sky-500/20 text-sky-400 border-sky-500/30",
  plumbing: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  electrical: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  power: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  civil: "bg-purple-500/20 text-purple-400 border-purple-500/30",
};

function ContractorsPageContent() {
  const { token: TOKEN } = useAuth();
  const [contractors, setContractors] = useState<ContractorOut[]>(MOCK_CONTRACTORS);
  const searchParams = useSearchParams();
  const highlightId = searchParams.get("highlight");

  // Form states
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [specializations, setSpecializations] = useState("");
  const [rating, setRating] = useState(4.5);
  const [responseTime, setResponseTime] = useState(2.0);
  const [successRate, setSuccessRate] = useState(95);
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    if (TOKEN) {
      contractorsApi.list(TOKEN)
        .then((res) => {
          const blended = [...res];
          MOCK_CONTRACTORS.forEach(m => {
            if (!blended.some(c => c.id === m.id)) {
              blended.push(m);
            }
          });
          setContractors(blended.filter(c => c.is_active));
        })
        .catch(() => setContractors(MOCK_CONTRACTORS));
    }
  }, [TOKEN]);

  // Smooth scroll highlighted contractor into view
  useEffect(() => {
    if (highlightId && contractors.length > 0) {
      const timer = setTimeout(() => {
        const cleanId = highlightId.replace(/[^a-zA-Z0-9]/g, "").toLowerCase();
        const target = contractors.find(
          c => c.id === highlightId || c.name.replace(/[^a-zA-Z0-9]/g, "").toLowerCase() === cleanId
        );
        
        if (target) {
          const el = document.getElementById(`contractor-${target.id}`);
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "center" });
          }
        }
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [highlightId, contractors]);

  const handleAddContractor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const specsArray = specializations.split(",").map(s => s.trim().toLowerCase()).filter(Boolean);

    const payload = {
      name,
      specializations: specsArray,
      rating: Number(rating),
      avg_response_time_hrs: Number(responseTime),
      success_rate: Number(successRate) / 100,
      total_jobs: 0,
      contact_info: { phone, email, address },
      is_active: true
    };

    try {
      if (TOKEN) {
        const res = await contractorsApi.create(TOKEN, payload);
        setContractors([res, ...contractors]);
      } else {
        throw new Error("No token");
      }
      setShowForm(false);
      setSuccessMsg(`Contractor "${name}" added successfully.`);
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch {
      // Local fallback simulation
      const mockNew: ContractorOut = {
        id: String(contractors.length + 1),
        ...payload
      };
      setContractors([mockNew, ...contractors]);
      setShowForm(false);
      setSuccessMsg(`Offline Fallback: Contractor "${name}" saved locally.`);
      setTimeout(() => setSuccessMsg(""), 3000);
    }

    // Reset fields
    setName("");
    setSpecializations("");
    setRating(4.5);
    setResponseTime(2.0);
    setSuccessRate(95);
    setPhone("");
    setEmail("");
    setAddress("");
  };

  const handleRemoveContractor = async (id: string) => {
    try {
      if (TOKEN) await contractorsApi.delete(TOKEN, id);
      setContractors(contractors.filter(c => c.id !== id));
      setSuccessMsg("Contractor removed successfully.");
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch {
      setContractors(contractors.filter(c => c.id !== id));
      setSuccessMsg("Offline Fallback: Contractor removed locally.");
      setTimeout(() => setSuccessMsg(""), 3000);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] p-5 lg:p-7 animate-fade-in space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Contractors</h1>
          <p className="text-sm text-zinc-400 mt-0.5">{contractors.length} registered contractors · ranked by AI selection score</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-sm font-medium text-white rounded-xl transition-colors cursor-pointer"
        >
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? "Cancel" : "Add Contractor"}
        </button>
      </div>

      {successMsg && (
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 p-4 rounded-xl text-xs transition-all animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {successMsg}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleAddContractor} className="max-w-2xl glass-card p-6 space-y-4 animate-fadeIn">
          <h2 className="text-base font-bold text-white">Register New Contractor</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Contractor Name</label>
              <input
                type="text" required value={name} onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Noida Power Grid Corp"
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Specializations (comma-separated)</label>
              <input
                type="text" required value={specializations} onChange={(e) => setSpecializations(e.target.value)}
                placeholder="e.g. water, plumbing, electrical"
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Rating (1.0 to 5.0)</label>
              <input
                type="number" step="0.1" min="1" max="5" value={rating} onChange={(e) => setRating(Number(e.target.value))}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Avg Response Time (hours)</label>
              <input
                type="number" step="0.1" min="0.1" value={responseTime} onChange={(e) => setResponseTime(Number(e.target.value))}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Success Rate (%)</label>
              <input
                type="number" min="1" max="100" value={successRate} onChange={(e) => setSuccessRate(Number(e.target.value))}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Phone</label>
              <input
                type="text" value={phone} onChange={(e) => setPhone(e.target.value)}
                placeholder="e.g. +91-9876543210"
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Email</label>
              <input
                type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. contact@npgc.com"
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Address</label>
              <input
                type="text" value={address} onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g. Sector 15, Noida"
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50"
              />
            </div>
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-sm font-medium text-white rounded-xl transition-colors cursor-pointer"
          >
            Save Contractor
          </button>
        </form>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {contractors.map((c) => {
          const cleanId = highlightId ? highlightId.replace(/[^a-zA-Z0-9]/g, "").toLowerCase() : "";
          const isHighlighted = highlightId && (
            c.id === highlightId || c.name.replace(/[^a-zA-Z0-9]/g, "").toLowerCase() === cleanId
          );

          return (
            <div 
              key={c.id} 
              id={`contractor-${c.id}`}
              className={`glass-card p-5 transition-all duration-500 ${
                isHighlighted
                  ? "border-violet-500/80 bg-violet-500/10 shadow-lg shadow-violet-500/20 scale-[1.01] ring-1 ring-violet-500/50"
                  : "hover:border-white/10"
              }`}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="text-base font-bold text-white">{c.name}</h2>
                    {c.is_active && (
                      <span className="flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/20 ring-1 ring-emerald-500/30 px-2 py-0.5 rounded-full">
                        <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" /> Active
                      </span>
                    )}
                  </div>
                  <StarRating rating={c.rating} />
                </div>
                <div className="flex items-start gap-3">
                  <div className="text-right">
                    <p className="text-2xl font-bold text-white">{(c.success_rate * 100).toFixed(0)}%</p>
                    <p className="text-[10px] text-zinc-400">Success rate</p>
                  </div>
                  <button
                    onClick={() => handleRemoveContractor(c.id)}
                    title="Remove Contractor"
                    className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500 hover:text-white transition-all cursor-pointer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Specializations */}
              <div className="flex flex-wrap gap-1.5 mb-4">
                {c.specializations.map((s) => (
                  <span key={s} className={`text-[10px] font-medium capitalize border px-2.5 py-1 rounded-full ${SPEC_COLORS[s] || "bg-zinc-800/50 text-zinc-400 border-white/[0.08]"}`}>{s}</span>
                ))}
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] p-3">
                  <div className="flex items-center gap-2 mb-1"><Clock className="w-3.5 h-3.5 text-amber-400" /><p className="text-[10px] text-zinc-400">Avg Response</p></div>
                  <p className="text-sm font-semibold text-zinc-200">{c.avg_response_time_hrs}h</p>
                </div>
                <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] p-3">
                  <div className="flex items-center gap-2 mb-1"><Briefcase className="w-3.5 h-3.5 text-violet-400" /><p className="text-[10px] text-zinc-400">Total Jobs</p></div>
                  <p className="text-sm font-semibold text-zinc-200">{c.total_jobs}</p>
                </div>
              </div>

              {/* Contact */}
              <div className="space-y-1.5 pt-3 border-t border-white/[0.06]">
                {c.contact_info.phone && (
                  <div className="flex items-center gap-2 text-xs text-zinc-400"><Phone className="w-3 h-3 text-zinc-400" />{c.contact_info.phone}</div>
                )}
                {c.contact_info.email && (
                  <div className="flex items-center gap-2 text-xs text-zinc-400"><Mail className="w-3 h-3 text-zinc-400" />{c.contact_info.email}</div>
                )}
                {c.contact_info.address && (
                  <div className="flex items-center gap-2 text-xs text-zinc-400"><MapPin className="w-3 h-3 text-zinc-400" />{c.contact_info.address}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ContractorsPage() {
  return (
    <Suspense fallback={<div className="p-6 text-zinc-400">Loading contractor listings...</div>}>
      <ContractorsPageContent />
    </Suspense>
  );
}
