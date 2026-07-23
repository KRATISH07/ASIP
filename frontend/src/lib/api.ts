const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string;
};

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, token } = opts;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  
  // Intercept the token: if the page passes 'demo-token', override with the stored JWT if available
  let activeToken = token;
  if (typeof window !== "undefined") {
    const stored = sessionStorage.getItem("asip_token");
    if (stored && (token === "demo-token" || !token)) {
      activeToken = stored;
    }
  }

  if (activeToken) headers["Authorization"] = `Bearer ${activeToken}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.detail || err.message || "Request failed");
  }

  return res.json() as Promise<T>;
}

// ── Auth ────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string; token_type: string }>(
      "/auth/login",
      { method: "POST", body: { email, password } }
    ),
  me: (token: string) =>
    request<{ id: string; email: string; role: string; full_name: string }>(
      "/auth/me",
      { token }
    ),
};

// ── Dashboard ────────────────────────────────────────────────────────────────
export const dashboardApi = {
  getSummary: (token: string) =>
    request<DashboardOut>("/dashboard/", { token }),
  getAnalytics: (token: string) =>
    request<AnalyticsOut>("/dashboard/analytics/", { token }),
};

// ── Incidents ────────────────────────────────────────────────────────────────
export const incidentsApi = {
  list: (token: string, params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<IncidentListOut>(`/incidents/${qs}`, { token });
  },
  get: (token: string, id: string) =>
    request<IncidentOut>(`/incidents/${id}`, { token }),
  create: (token: string, data: any) =>
    request<IncidentOut>("/incidents/", {
      method: "POST", body: data, token,
    }),
  updateStatus: (token: string, id: string, status: string) =>
    request<IncidentOut>(`/incidents/${id}/status`, {
      method: "PATCH", body: { status }, token,
    }),
  ingestSensor: (token: string, data: SensorDataPayload) =>
    request<{ message: string; incident_id?: string }>("/incidents/sensor-data", {
      method: "POST", body: data, token,
    }),
  submitFeedback: (token: string, id: string, data: any) =>
    request<any>(`/incidents/${id}/feedback`, {
      method: "POST", body: data, token,
    }),
};

// ── Contractors ───────────────────────────────────────────────────────────────
export const contractorsApi = {
  list: (token: string) =>
    request<ContractorOut[]>("/contractors/", { token }),
  get: (token: string, id: string) =>
    request<ContractorOut>(`/contractors/${id}`, { token }),
  getRankings: (token: string, incidentType: string, k: number = 3) =>
    request<any[]>(`/contractors/rankings?incident_type=${incidentType}&k=${k}`, { token }),
  create: (token: string, data: any) =>
    request<ContractorOut>("/contractors/", { method: "POST", body: data, token }),
  delete: (token: string, id: string) =>
    request<any>(`/contractors/${id}`, { method: "DELETE", token }),
};

// ── Notifications ─────────────────────────────────────────────────────────────
export const notificationsApi = {
  list: (token: string) =>
    request<NotificationOut[]>("/notifications/", { token }),
  send: (token: string, id: string) =>
    request<{ message: string; id: string }>(`/notifications/${id}/send`, {
      method: "POST", token,
    }),
  delete: (token: string, id: string) =>
    request<any>(`/notifications/${id}`, { method: "DELETE", token }),
};

// ── Agent Logs ────────────────────────────────────────────────────────────────
export const agentLogsApi = {
  list: (token: string) =>
    request<AgentLogOut[]>("/agent-logs/", { token }),
  byIncident: (token: string, incidentId: string) =>
    request<AgentLogOut[]>(`/agent-logs/${incidentId}`, { token }),
};

// ── Complaints ────────────────────────────────────────────────────────────────
export const complaintsApi = {
  create: (token: string, data: { title: string; description: string; category: string; priority: string }) =>
    request<any>("/complaints/", { method: "POST", body: data, token }),
  listMine: (token: string, page: number = 1, pageSize: number = 20) =>
    request<any>(`/complaints/mine?page=${page}&page_size=${pageSize}`, { token }),
  listAll: (token: string, status?: string, category?: string, page: number = 1, pageSize: number = 20) => {
    let url = `/complaints/?page=${page}&page_size=${pageSize}`;
    if (status) url += `&status=${status}`;
    if (category) url += `&category=${category}`;
    return request<any>(url, { token });
  },
  get: (token: string, id: string) =>
    request<any>(`/complaints/${id}`, { token }),
  update: (token: string, id: string, data: any) =>
    request<any>(`/complaints/${id}`, { method: "PATCH", body: data, token }),
  convert: (token: string, id: string, data: { incident_type?: string; override_severity?: string }) =>
    request<any>(`/complaints/${id}/convert`, { method: "POST", body: data, token }),
  getStats: (token: string) =>
    request<any>("/complaints/stats", { token }),
};

// ── Sensor Buffer ─────────────────────────────────────────────────────────────
export const sensorBufferApi = {
  upload: (token: string, events: any[]) =>
    request<any>("/sensor-buffer/upload", { method: "POST", body: { events }, token }),
  replay: (token: string, limit: number = 50) =>
    request<any>("/sensor-buffer/replay", { method: "POST", body: { limit }, token }),
  getStats: (token: string) =>
    request<any>("/sensor-buffer/stats", { token }),
};

// ── Types ─────────────────────────────────────────────────────────────────────
export interface DashboardOut {
  kpi: { total_incidents: number; active_incidents: number; critical_incidents: number; resolved_today: number; avg_resolution_time_hrs?: number };
  recent_incidents: RecentIncident[];
  agent_activity: AgentActivity[];
  severity_distribution: Record<string, number>;
  incident_trend: { date: string; count: number }[];
}
export interface AnalyticsOut {
  incident_trend: { date: string; count: number }[];
  severity_distribution: Record<string, number>;
  incident_type_distribution: Record<string, number>;
  resolution_time_trend: { date: string; avg_hours: number }[];
  contractor_performance: { name: string; jobs: number; rating: number }[];
}
export interface RecentIncident { id: string; type: string; severity: string; status: string; tower_name?: string; detected_at: string; }
export interface AgentActivity { agent_name: string; executions_today: number; avg_execution_time_ms?: number; success_rate: number; }
export interface AiDecision {
  incident_summary?: string;
  root_cause?: string;
  impact_summary?: string;
  action_plan?: string;
  estimated_resolution_hrs?: number;
  priority?: string;
  prediction?: { predicted_residents?: number; predicted_outage_hrs?: number; estimated_cost?: number; confidence_score?: number; escalation_probability?: number; sla_breach_risk?: number; estimated_contractor_cost?: number };
  decision?: { auto_dispatch?: boolean; risk_score?: number; requires_escalation?: boolean; notify_residents?: boolean; notification_priority?: string; recommended_contractor?: string; backup_activation?: boolean };
  probable_cause?: string;
  contractor?: string;
  [key: string]: unknown;
}
export interface IncidentOut { id: string; type: string; severity: string; confidence: number; status: string; tower_id?: string; tower_name?: string; description?: string; root_cause?: string; ai_decision?: AiDecision; detected_at: string; resolved_at?: string; sensor_data?: { manual_report?: boolean; reported_by?: string; custom_type?: string; [key: string]: unknown }; contractor_assignment?: ContractorAssignmentOut; }
export interface IncidentListOut { items: IncidentOut[]; total: number; page: number; page_size: number; }
export interface ContractorAssignmentOut { contractor_id?: string; contractor_name: string; estimated_cost?: number; estimated_time_hrs?: number; selection_reasoning?: string; }
export interface ContractorOut { id: string; name: string; specializations: string[]; rating: number; avg_response_time_hrs: number; total_jobs: number; success_rate: number; contact_info: Record<string, string>; is_active: boolean; }
export interface NotificationOut { id: string; incident_id: string; channel: string; subject?: string; content: string; status: string; sent_at?: string; }
export interface AgentLogOut { id: string; incident_id: string; agent_name: string; execution_time_ms?: number; tokens_used?: number; status: string; error?: string; input_payload?: Record<string, unknown>; output_payload?: Record<string, unknown>; created_at: string; }
export interface SensorDataPayload { tower_id: string; sensor_type: string; value: number; unit: string; timestamp: string; }
