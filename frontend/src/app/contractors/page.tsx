"use client";

import { useEffect, useState } from "react";
import { contractorsApi, type ContractorOut } from "@/lib/api";
import { Star, Clock, Briefcase, Phone, Mail, MapPin, CheckCircle2 } from "lucide-react";

const TOKEN = "demo-token";

const MOCK_CONTRACTORS: ContractorOut[] = [
  { id: "1", name: "AquaFix Pro", specializations: ["water", "plumbing"], rating: 4.8, avg_response_time_hrs: 2.0, total_jobs: 145, success_rate: 0.97, contact_info: { phone: "+91-9876543210", email: "aquafix@example.com", address: "Sector 12, Noida" }, is_active: true },
  { id: "2", name: "PowerSure Services", specializations: ["electrical", "power"], rating: 4.6, avg_response_time_hrs: 1.5, total_jobs: 203, success_rate: 0.95, contact_info: { phone: "+91-9123456780", email: "powersure@example.com", address: "Sector 18, Gurugram" }, is_active: true },
  { id: "3", name: "CityFix General", specializations: ["water", "electrical", "civil"], rating: 4.2, avg_response_time_hrs: 3.5, total_jobs: 87, success_rate: 0.89, contact_info: { phone: "+91-9988776655", email: "cityfix@example.com", address: "Sector 5, Delhi" }, is_active: true },
  { id: "4", name: "RapidRepair Elite", specializations: ["water", "electrical"], rating: 4.9, avg_response_time_hrs: 1.0, total_jobs: 312, success_rate: 0.98, contact_info: { phone: "+91-9001234567", email: "rapid@example.com", address: "Sector 62, Noida" }, is_active: true },
];

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((s) => (
        <Star key={s} className={`w-3.5 h-3.5 ${s <= Math.round(rating) ? "text-yellow-400 fill-yellow-400" : "text-gray-600"}`} />
      ))}
      <span className="text-xs text-gray-400 ml-1">{rating.toFixed(1)}</span>
    </div>
  );
}

const SPEC_COLORS: Record<string, string> = {
  water: "bg-blue-500/20 text-blue-400 border-blue-500/20",
  plumbing: "bg-cyan-500/20 text-cyan-400 border-cyan-500/20",
  electrical: "bg-yellow-500/20 text-yellow-400 border-yellow-500/20",
  power: "bg-amber-500/20 text-amber-400 border-amber-500/20",
  civil: "bg-purple-500/20 text-purple-400 border-purple-500/20",
};

export default function ContractorsPage() {
  const [contractors, setContractors] = useState<ContractorOut[]>(MOCK_CONTRACTORS);

  useEffect(() => {
    contractorsApi.list(TOKEN).then(setContractors).catch(() => setContractors(MOCK_CONTRACTORS));
  }, []);

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Contractors</h1>
          <p className="text-sm text-gray-400 mt-0.5">{contractors.length} registered contractors · ranked by AI selection score</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {contractors.map((c) => (
          <div key={c.id} className="rounded-2xl border border-white/5 bg-white/3 backdrop-blur-xl p-5 hover:border-white/10 transition-all">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="text-base font-bold text-white">{c.name}</h2>
                  {c.is_active && (
                    <span className="flex items-center gap-1 text-[10px] text-green-400 bg-green-500/10 border border-green-500/20 px-2 py-0.5 rounded-full">
                      <CheckCircle2 className="w-2.5 h-2.5" /> Active
                    </span>
                  )}
                </div>
                <StarRating rating={c.rating} />
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-white">{(c.success_rate * 100).toFixed(0)}%</p>
                <p className="text-[10px] text-gray-500">Success rate</p>
              </div>
            </div>

            {/* Specializations */}
            <div className="flex flex-wrap gap-1.5 mb-4">
              {c.specializations.map((s) => (
                <span key={s} className={`text-[10px] font-medium capitalize border px-2.5 py-1 rounded-full ${SPEC_COLORS[s] || "bg-gray-500/20 text-gray-400"}`}>{s}</span>
              ))}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="rounded-xl bg-white/3 border border-white/5 p-3">
                <div className="flex items-center gap-2 mb-1"><Clock className="w-3.5 h-3.5 text-blue-400" /><p className="text-[10px] text-gray-500">Avg Response</p></div>
                <p className="text-sm font-semibold text-white">{c.avg_response_time_hrs}h</p>
              </div>
              <div className="rounded-xl bg-white/3 border border-white/5 p-3">
                <div className="flex items-center gap-2 mb-1"><Briefcase className="w-3.5 h-3.5 text-violet-400" /><p className="text-[10px] text-gray-500">Total Jobs</p></div>
                <p className="text-sm font-semibold text-white">{c.total_jobs}</p>
              </div>
            </div>

            {/* Contact */}
            <div className="space-y-1.5 pt-3 border-t border-white/5">
              {c.contact_info.phone && (
                <div className="flex items-center gap-2 text-xs text-gray-400"><Phone className="w-3 h-3" />{c.contact_info.phone}</div>
              )}
              {c.contact_info.email && (
                <div className="flex items-center gap-2 text-xs text-gray-400"><Mail className="w-3 h-3" />{c.contact_info.email}</div>
              )}
              {c.contact_info.address && (
                <div className="flex items-center gap-2 text-xs text-gray-400"><MapPin className="w-3 h-3" />{c.contact_info.address}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
