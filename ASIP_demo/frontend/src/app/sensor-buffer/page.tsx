"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { sensorBufferApi } from "@/lib/api";
import {
  Cpu, RotateCw, CheckCircle2, AlertTriangle, Play, RefreshCw, BarChart2, Plus, Terminal
} from "lucide-react";

interface BufferStats {
  total_events: number;
  pending_events: number;
  synced_events: number;
  failed_events: number;
  oldest_pending_age_sec?: number;
  success_rate: number;
}

export default function SensorBufferPage() {
  const { token } = useAuth();
  
  const [stats, setStats] = useState<BufferStats>({
    total_events: 0, pending_events: 0, synced_events: 0, failed_events: 0, success_rate: 1.0
  });
  const [loading, setLoading] = useState(true);
  const [replaySubmitting, setReplaySubmitting] = useState(false);
  const [replayResult, setReplayResult] = useState<string | null>(null);
  
  // Simulator states
  const [sensorId, setSensorId] = useState("flow-meter-A1");
  const [value, setValue] = useState("1.8");
  const [unit, setUnit] = useState("bar");
  const [simulatorResult, setSimulatorResult] = useState<string | null>(null);
  const [simulating, setSimulating] = useState(false);

  const fetchStats = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const res = await sensorBufferApi.getStats(token);
      setStats(res);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [token]);

  const triggerReplay = async () => {
    if (!token) return;
    setReplaySubmitting(true);
    setReplayResult(null);
    try {
      const res = await sensorBufferApi.replay(token, 20);
      setReplayResult(`Replayed: ${res.replayed} events. Succeeded: ${res.succeeded}. Failed: ${res.failed}.`);
      fetchStats();
    } catch (err: any) {
      setReplayResult(`Error replaying: ${err.message}`);
    } finally {
      setReplaySubmitting(false);
    }
  };

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setSimulating(true);
    setSimulatorResult(null);

    const event = {
      sensor_id: sensorId,
      idempotency_key: `sim-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      payload: {
        tower_id: "df7163dc-c593-42a6-9993-ecc1acc2002b", // default seeded Tower A ID
        sensor_type: "water_pressure",
        value: parseFloat(value),
        unit: unit,
        timestamp: new Date().toISOString(),
      },
      event_timestamp: new Date().toISOString(),
    };

    try {
      const res = await sensorBufferApi.upload(token, [event]);
      setSimulatorResult(`Uploaded 1 event to durable buffer. Total received: ${res.total_received}, duplicates skipped: ${res.duplicate_skipped}.`);
      fetchStats();
    } catch (err: any) {
      setSimulatorResult(`Failed to simulate upload: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] p-5 lg:p-7 animate-fade-in space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="glass-card p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400 flex items-center justify-center">
            <Cpu className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">IoT Edge Gateway Portal</h1>
            <p className="text-xs text-zinc-400 mt-1">
              Durable Store-and-Forward ingestion diagnostics &bull; Gateway ID: <span className="font-mono text-zinc-200">gw-gate-3092</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs font-semibold text-emerald-400 ring-1 ring-emerald-500/30">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping"></span>
          <p>Connected</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Metric Cards */}
        <div className="glass-card p-5 space-y-2">
          <p className="text-xs text-zinc-400 uppercase tracking-wider">Total Buffer Uploads</p>
          <p className="text-3xl font-bold text-white tabular-nums">{stats.total_events}</p>
          <p className="text-[10px] text-zinc-500">Cumulative historical uploads</p>
        </div>
        <div className="glass-card p-5 space-y-2">
          <p className="text-xs text-zinc-400 uppercase tracking-wider">Unsynced Pending</p>
          <p className="text-3xl font-bold text-amber-400 tabular-nums">{stats.pending_events}</p>
          <p className="text-[10px] text-zinc-500">Awaiting automatic loop upload</p>
        </div>
        <div className="glass-card p-5 space-y-2">
          <p className="text-xs text-zinc-400 uppercase tracking-wider">Failed / Retrying</p>
          <p className="text-3xl font-bold text-rose-400 tabular-nums">{stats.failed_events}</p>
          <p className="text-[10px] text-zinc-500">Requires manual replay review</p>
        </div>
        <div className="glass-card p-5 space-y-2">
          <p className="text-xs text-zinc-400 uppercase tracking-wider">Ingestion Success Rate</p>
          <p className="text-3xl font-bold text-emerald-400 tabular-nums">{(stats.success_rate * 100).toFixed(1)}%</p>
          <p className="text-[10px] text-zinc-500">Replay compilation success</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Replay Controls (Left) */}
        <div className="lg:col-span-1 glass-card p-6 space-y-6">
          <div>
            <div className="flex items-center gap-2">
              <RotateCw className="h-5 w-5 text-amber-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">Manual Replay Trigger</h2>
            </div>
            <p className="text-xs text-zinc-400 mt-1">Force compile and process failed buffer records into active incidents.</p>
          </div>

          <div className="p-4 bg-white/[0.03] border border-white/[0.06] rounded-xl space-y-3">
            <p className="text-xs text-zinc-300">
              When edge sensors experience network failures, events accumulate locally. If automatic loops stall, trigger a manual replay here.
            </p>
            <button
              onClick={triggerReplay}
              disabled={replaySubmitting || stats.failed_events === 0}
              className="w-full py-3 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:bg-white/[0.04] disabled:text-zinc-500 disabled:border-white/[0.06] text-white text-sm font-semibold transition flex items-center justify-center gap-2 border border-amber-500/30"
            >
              {replaySubmitting ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {replaySubmitting ? "Running Replay..." : "Trigger Replay"}
            </button>
          </div>

          {replayResult && (
            <div className="p-4 bg-black/40 rounded-xl border border-white/[0.08] flex items-start gap-2 text-xs font-mono text-zinc-300 leading-snug">
              <Terminal className="h-4.5 w-4.5 text-amber-400 flex-shrink-0 mt-0.5" />
              <span>{replayResult}</span>
            </div>
          )}
        </div>

        {/* Telemetry Simulator Form (Right) */}
        <div className="lg:col-span-2 glass-card p-6 space-y-6">
          <div>
            <div className="flex items-center gap-2">
              <Plus className="h-5 w-5 text-violet-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">Durable Buffer Ingestion Simulator</h2>
            </div>
            <p className="text-xs text-zinc-400 mt-1">Simulate network drop uploads. Telemetry is saved with idempotency keys.</p>
          </div>

          <form onSubmit={handleSimulate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
                Sensor Identifier
              </label>
              <input
                type="text"
                value={sensorId}
                onChange={(e) => setSensorId(e.target.value)}
                placeholder="flow-meter-A1"
                className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 transition"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
                Telemetry Value
              </label>
              <input
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="1.8"
                className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 transition"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
                Unit of Measure
              </label>
              <input
                type="text"
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                placeholder="bar"
                className="w-full px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.08] text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-violet-500/50 transition"
                required
              />
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={simulating}
                className="w-full py-3 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:bg-violet-600/50 text-white text-sm font-semibold transition border border-violet-500/30"
              >
                {simulating ? "Uploading..." : "Inject Simulated Telemetry"}
              </button>
            </div>
          </form>

          {simulatorResult && (
            <div className="p-4 bg-black/40 rounded-xl border border-white/[0.08] flex items-start gap-2 text-xs font-mono text-zinc-300 leading-snug">
              <Terminal className="h-4.5 w-4.5 text-violet-400 flex-shrink-0 mt-0.5" />
              <span>{simulatorResult}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
